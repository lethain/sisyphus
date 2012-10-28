"""
Sisyphus models are stored in Redis.

Primarily, we're interested in Tags, Pages and Traffic.

Tags are ordered sets of Pages, which are ordered
by both the date a Page was added to a Tag as well
as their popularity within that Tag (accomplished
via two sorted-sets in Redis).

Pages are JSON blobs stored as strings.

Traffic is per Tag, per Page and overall site traffic,
bucketed for the last 60 minutes, the last 24 hours,
the last 7 days, last 4 weeks and lifespan.

"""

from django.conf import settings

import redis
import time
import datetime
import whoosh.index
import whoosh.fields
import whoosh.qparser
try:
    import json
except ImportError:
    import simplejson as json
import sisyphus.analytics

EMPTY_ZSET = "empty_zset"
TAG_ZSET_BY_TIME = "tags_by_times"
TAG_ZSET_BY_PAGES = "tags_by_pages"
TAG_PAGES_ZSET_BY_TIME = "tag_pages_by_time.%s"
TAG_PAGES_ZSET_BY_TREND = "tag_pages_by_trend.%s"
PAGE_ZSET_BY_TIME = "pages_by_time"
PAGE_ZSET_BY_TREND = "pages_by_trend"
PAGE_STRING = "page.%s"
SIMILAR_PAGES_BY_TREND = "similar_pages.%s"
SIMILAR_PAGES_EXPIRE = 60 * 5

PAGEVIEW_BONUS = 60 * 60 * 24

PAGE_SCHEMA = whoosh.fields.Schema(title=whoosh.fields.TEXT(),
                                   summary=whoosh.fields.TEXT(),
                                   content=whoosh.fields.TEXT(),
                                   slug=whoosh.fields.ID(unique=True, stored=True),
                                   )



def timebucket(period=3600):
    "Return current time bucket."
    return int(time.time()) / period

def track(request, page, cli=None):
    "Log pageview into analytics."
    slug = page['slug']
    # update trending data
    cli.zincrby(PAGE_ZSET_BY_TREND, slug, PAGEVIEW_BONUS)
    for tag_slug in page['tags']:
        cli.zincrby(TAG_PAGES_ZSET_BY_TREND % tag_slug[1], slug, PAGEVIEW_BONUS)
    if settings.REALTIME_ANALYTICS:
        sisyphus.analytics.track(request, page, cli)

def search(raw_query, cli=None):
    whoosh_index = whoosh.index.open_dir(settings.WHOOSH_INDEXDIR)
    pages = []
    searcher = None
    try:
        searcher = whoosh_index.searcher()
        query = whoosh.qparser.QueryParser('content', PAGE_SCHEMA).parse(raw_query)
        search_resp = searcher.search(query, limit=None)
        slugs = [ x['slug'] for x in search_resp ]
        if slugs:
            cli = cli or redis_client()
            pages = [ add_tag_counts(json.loads(y)) for y in cli.mget([ PAGE_STRING % x for x in slugs]) ]
    finally:
        if searcher is not None:
            searcher.close()
    return pages


def redis_client(host="localhost", port=6379, db=0):
    return redis.Redis(host, port, db=db)

def add_tag_counts(page, cli=None):
    "Extend page with tag counts."
    cli = cli or redis_client()
    tags = page['tags']
    if tags:
        pipeline = cli.pipeline()
        for tag in tags:
            pipeline.zscore(TAG_ZSET_BY_PAGES, tag)
        scores = [ x or 0 for x in pipeline.execute() ]
        page['tags'] = sorted(zip([ int(x) for x in scores], tags), reverse=True)
    return page

def get_page(page_slug, cli=None):
    "Retrieve a page."
    cli = cli or redis_client()
    resp = cli.get(PAGE_STRING % page_slug)
    return resp and add_tag_counts(json.loads(resp)) or resp

def add_tag(slug, created=None, cli=None):
    "Idempotently create a new tag."
    cli = cli or redis_client()
    if cli.zrank(TAG_ZSET_BY_TIME, slug) is None:
        created = created or int(time.time())
        cli.zadd(TAG_ZSET_BY_TIME, slug, created)

def add_page_to_tag(tag_slug, page_slug, created=None, cli=None):
    "Idempotently add a page to a tag."
    cli = cli or redis_client()
    if cli.zrank(TAG_PAGES_ZSET_BY_TIME % tag_slug, page_slug) is None:
        created = created or int(time.time())
        cli.zadd(TAG_PAGES_ZSET_BY_TIME % tag_slug, page_slug, created)
        cli.zadd(TAG_PAGES_ZSET_BY_TREND % tag_slug, page_slug, created)
        cli.zincrby(TAG_ZSET_BY_PAGES, tag_slug, 1)

def index_page(page):
    """
    Create a search index for this page. Mostly useful if recreating
    Sisyphus from a Redis snapshot but missing Whoosh index, e.g:

        [index_page(x) for x in get_pages(0, 100000)]

    Would reindex the 100k most recent posts.
    """
    try:
        whoosh_index = whoosh.index.open_dir(settings.WHOOSH_INDEXDIR)
    except Exception, e:
        whoosh_index = whoosh.index.create_in(settings.WHOOSH_INDEXDIR, PAGE_SCHEMA)
    writer = whoosh_index.writer()
    to_index = {'title': page['title'], 'summary':page['summary'], 'content':page['html'], 'slug':page['slug']}
    writer.update_document(**to_index)
    writer.commit()


def add_page(page, index=True, cli=None):
    """
    Create a page.

    Set index parameter to False if you want to load a page
    but don't want to associate it with any of the existing storylists.
    """
    cli = cli or redis_client()
    slug = page['slug']
    old_page = get_page(slug)

    if index and old_page and not old_page.get('published', False):
        page['pub_date'] = int(time.time())

    if old_page and old_page['html'] != page['html']:
        page['edit_date'] = int(time.time())
    elif old_page and 'edit_date' in old_page:
        page['edit_date'] = old_page['edit_date']
    else:
        page['edit_date'] = page['pub_date']

    page['published'] = False
    if index:
        page['published'] = True
        cli.zadd(PAGE_ZSET_BY_TIME, slug, page['pub_date'])
        cli.zadd(PAGE_ZSET_BY_TREND, slug, page['pub_date'])

        for tag in page['tags']:
            add_page_to_tag(tag, slug, created=page['pub_date'], cli=cli)

        index_page(page)

    cli.set(PAGE_STRING % slug, json.dumps(page))

def get_page_slugs(offset=0, limit=10, key=PAGE_ZSET_BY_TIME, reverse=True, cli=None, withscores=False):
    "Retrieve pages from global zsets."
    cli = cli or redis_client()
    if reverse:
        return cli.zrevrange(key, offset, offset+limit-1, withscores=withscores)
    else:
        return cli.zrange(key, offset, offset+limit-1, withscores=withscores)

def get_pages(offset=0, limit=10, key=PAGE_ZSET_BY_TIME, reverse=True, cli=None):
    "Retrieve pages data."
    cli = cli or redis_client()
    page_slugs = get_page_slugs(offset, limit, key, reverse, cli)
    if page_slugs:
        return [ add_tag_counts(json.loads(y)) for y in cli.mget([ PAGE_STRING % x for x in page_slugs]) ]
    else:
        return []

def get_nearby_pages(page, limit=3, cli=None):
    "Retrieve preceeding and following articles."
    slug = page['slug']
    pub_date = page['pub_date']
    cli = cli or redis_client()
    key = PAGE_ZSET_BY_TIME
    rank = cli.zrank(key, slug)
    start = max(rank-limit, 0)
    end = max(limit, rank+limit)
    page_slugs = cli.zrange(key, start, end)

    if page_slugs:
        return [ json.loads(y) for y in cli.mget([ PAGE_STRING % x for x in page_slugs]) ]
    else:
        return []

def ensure_similar_pages_key(page, cli=None):
    "Make sure the data exists."
    cli = cli or redis_client()
    sim_key = SIMILAR_PAGES_BY_TREND % page['slug']
    if not cli.exists(sim_key):
        tag_keys = [ TAG_PAGES_ZSET_BY_TREND % x[1] for x in page.get('tags',[])]
        if tag_keys:
            cli.zunionstore(sim_key, tag_keys)
            cli.zrem(sim_key, page['slug'])
            cli.expire(sim_key, SIMILAR_PAGES_EXPIRE)
        else:
            return None
    return sim_key

def similar_pages(page, offset=0, limit=3, withscores=False, cli=None):
    "Find top performing stories in similar tags."
    cli = cli or redis_client()
    sim_key = ensure_similar_pages_key(page, cli=cli)
    if sim_key:
        page_slugs = cli.zrevrange(sim_key, offset, offset+limit-1, withscores=withscores)
        if page_slugs:
            return [ json.loads(y) for y in cli.mget([ PAGE_STRING % x for x in page_slugs]) ]
    return []

def tags(offset=0, limit=10, withscores=True, cli=None):
    cli = cli or redis_client()
    resp = cli.zrevrange(TAG_ZSET_BY_PAGES, offset, offset+limit-1, withscores=withscores)
    if withscores:
        resp = [ (x,int(y)) for x,y in resp ]
    return resp

def convert_pub_date_to_datetime(page):
    "Replace timestamps with datetimes."
    page['pub_date'] = datetime.datetime.fromtimestamp(page['pub_date'])
    page['edit_date'] = datetime.datetime.fromtimestamp(page['edit_date'])
    return page

def num_pages(key=PAGE_ZSET_BY_TIME, cli=None):
    "Return cardinality for key."
    cli = cli or redis_client()
    return cli.zcard(key)

