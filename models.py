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
import redis
import time
import datetime
try:
    import json
except ImportError:
    import simplejson as json

TAG_ZSET_BY_TIME = "tags_by_times"
TAG_ZSET_BY_PAGES = "tags_by_pages"
TAG_PAGES_ZSET_BY_TIME = "tag_pages_by_time.%s"
TAG_PAGES_ZSET_BY_TREND = "tag_pages_by_trend.%s"
PAGE_ZSET_BY_TIME = "pages_by_time"
PAGE_ZSET_BY_TREND = "pages_by_trend"
PAGE_STRING = "page.%s"

def redis_client(host="localhost", port=6379, db=0):
    return redis.Redis(host, port, db=db)

def add_tag(slug, created=None, cli=None):
    "Idempotently create a new tag."
    cli = cli or redis_client()
    if cli.zrank(TAG_ZSET_BY_TIME, slug) is None:
        created = created or int(time.time())
        cli.zadd(TAG_ZSET_BY_TIME, slug, created)
        cli.zadd(TAG_ZSET_BY_PAGES, slug, 0)

def add_page_to_tag(tag_slug, page_slug, created=None, cli=None):
    "Idempotently add a page to a tag."
    cli = cli or redis_client()
    if cli.zrank(TAG_PAGES_ZSET_BY_TIME % tag_slug, page_slug) is None:
        created = created or int(time.time())
        cli.zadd(TAG_PAGES_ZSET_BY_TIME % tag_slug, page_slug, created)
        cli.zadd(TAG_PAGES_ZSET_BY_TREND % tag_slug, page_slug, created)

def add_page(page, cli=None):
    "Create a page."
    cli = cli or redis_client()
    slug = page['slug']
    cli.set(PAGE_STRING % slug, json.dumps(page))
    cli.zadd(PAGE_ZSET_BY_TIME, slug, page['pub_date'])
    cli.zadd(PAGE_ZSET_BY_TREND, slug, page['pub_date'])

    for tag in page['tags']:
        add_page_to_tag(tag, slug, created=page['pub_date'], cli=cli)

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
    return [ json.loads(y) for y in cli.mget([ PAGE_STRING % x for x in page_slugs]) ]

def convert_pub_date_to_datetime(page):
    "Replace timestamps with datetimes."
    page['pub_date'] = datetime.datetime.fromtimestamp(page['pub_date'])
    return page

def num_pages(key=PAGE_ZSET_BY_TIME, cli=None):
    "Return cardinality for key."
    cli = cli or redis_client()
    return cli.zcard(key)

# import sisyphus.models; reload(sisyphus.models); sisyphus.models.get_pages(0, 10)    
# python ./scripts/import_from_lifeflow.py < today.json

def get_page(page_slug, cli=None):
    "Retrieve a page."
    pass
