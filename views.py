"Views for blog application."
from django.shortcuts import render_to_response
from django.http import HttpResponse, Http404
from django.template import RequestContext
from django.conf import settings
import sisyphus.models
import django.utils.feedgenerator

STORY_LIST_KEYS = { 'recent': sisyphus.models.PAGE_ZSET_BY_TIME,
                    'trending': sisyphus.models.PAGE_ZSET_BY_TREND,
                    }

STORY_LIST_TITLES = { 'recent': "Recent pages",
                      'trending': "Popular pages"
                      }
TAG_LIST_TITLE = "Pages tagged with %s"

def tag_feed(request, tag_slug):
    "Return RSS feed for a given tag."
    tag_slug = tag_slug.rstrip("/")
    cli = sisyphus.models.redis_client()
    key = sisyphus.models.TAG_PAGES_ZSET_BY_TREND % tag_slug
    page_dicts = sisyphus.models.get_pages(limit=25, key=key, cli=cli)
    return generate_feed(request, page_dicts, cli)
    
def feed(request, feed_url):
    "Return RSS feed of recent pages."
    cli = sisyphus.models.redis_client()
    page_dicts = sisyphus.models.get_pages(limit=25, cli=cli)
    return generate_feed(request, page_dicts, cli)

def generate_feed(request, page_dicts, cli):
    page_dicts = [ sisyphus.models.convert_pub_date_to_datetime(x) for x in page_dicts ]
    f = django.utils.feedgenerator.Rss201rev2Feed(
        title=settings.RSS_TITLE,
        link=settings.RSS_LINK,
        description=settings.RSS_DESC,
        language=settings.RSS_LANG,
        author_name=settings.RSS_AUTHOR,
        feed_url=settings.RSS_FEED_URL,
        )
    cli = sisyphus.models.redis_client()
    for page in page_dicts:
        f.add_item(title=page['title'],
                   link="http://%s/%s/" % (settings.DOMAIN, page['slug']),
                   pubdate=page['pub_date'],
                   description=page['html'],
                   )
    return HttpResponse(f.writeString('UTF-8'), mimetype="application/rss+xml")

def about_module(cli=None):
    "An 'About Me' module."
    html = """<img src="/static/author.png">
<p>Your delightful host.<br>
Email: lethain[at]gmail<br>
Develop at <a href="http://digg.com/">Digg</a>.<br>
Used to <a href="http://developer.yahoo.com/search/boss/">Yahoo! BOSS</a>.</p>"""
    return { 'title':'Will Larson', 'html':html }

def analytics_module(cli=None):
    "Analytics module."
    html = """<p>Recent activity&hellip;</p>"""
    # return { 'title':'Analytics', 'html':html }
    return None

def storylist_module(key, title, more_link=None, limit=3, cli=None, page=None):
    cli = cli or sisyphus.models.redis_client()
    limit = limit + 1 if page else limit
    objects = sisyphus.models.get_pages(limit=limit, key=key, cli=cli)
    if page and 'slug' in page:
        objects = [ x for x in objects if x['slug'] != page['slug'] ][:limit]

    return { 'title': title, 'pages': objects, 'more_link': more_link }

def trending_module(limit=3, page=None, cli=None):
    "Create default trending module."
    return storylist_module(sisyphus.models.PAGE_ZSET_BY_TREND,
                            "Popular",
                            "/list/trending/",
                            limit=limit,
                            page=page)

def tags_list(request):
    cli = sisyphus.models.redis_client()

    # 'nav_tags': sisyphus.models.tags(limit=getattr(settings,'NUM_TAGS_NAV', 8), cli=cli),

    tags = sisyphus.models.tags(limit=1000, cli=cli)
    context = {'tags': tags,
               'html_title':"Tags ordered by number of pages",
               'nav_tags': tags[:getattr(settings,'NUM_TAGS_NAV', 8)],
               'modules': default_modules(None, limit=5, cli=cli)
               }
    return render_to_response('sisyphus/tag_list.html', context, context_instance=RequestContext(request))

def tags_module(offset=0, limit=10, cli=None):
    "Create module for tags."
    tags = sisyphus.models.tags(offset, limit, cli=cli)
    html = ['<ul class="tags">'] + \
        [ '<li><a href="/tags/%s/">%s</a> (%s)</li>' % (x,x,y) for x,y in tags ] + \
        ['<li><a href="/tags/">More&hellip;</a></li>', '</ul>']
    return { 'title': 'Tags', 'html':'\n'.join(html) }

def recent_module(limit=3, page=None, cli=None):
    "Create default trending module."
    return storylist_module(sisyphus.models.PAGE_ZSET_BY_TIME,
                            "Recent",
                            "/list/recent/",
                            limit=limit,
                            page=page)

def context_module(page, limit=2, cli=None):
    "Module contains stories surrounding."
    pages = sisyphus.models.get_nearby_pages(page, limit, cli=cli)
    before = None
    after = None
    if pages[:limit]:
        before = {"title":"Previous", "pages":reversed(pages[:limit])}
    if pages[limit+1:]:
        after = {"title":"Next", "pages":pages[limit+1:]}
    return (before, after)

def similar_pages_module(page, limit=3, cli=None):
    """
    Find stories which have a high overlap of tags with this one,
    then also sort by those articles' trending scores.
    """
    pages = sisyphus.models.similar_pages(page, limit=limit, cli=cli)
    if pages:
        more_link = '/similar/%s/' % page['slug'] if len(pages) >= limit else None
        return {'title': 'Similar', 'pages':pages, 'more_link':more_link}
    else:
        return None

def default_modules(page, extras=[], limit=3, cli=None):
    ""
    modules = [(0.75, about_module(cli=cli)),
               (0.5, trending_module(limit=limit, page=page, cli=cli)),
               (0.25, recent_module(limit=limit, page=page, cli=cli)),
               ]
    modules += extras
    active_modules = [ (x,y) for x,y in modules if y ]
    active_modules.sort(reverse=True)
    return [ y for x,y in active_modules ]

def render_list(request, key, base_url, title, cli=None):
    try:
        offset = int(request.GET.get('offset', 0))
    except ValueError:
        offset = 0
    try:
        limit = int(request.GET.get('limit', 10))
    except ValueError:
        limit = 10

    page_dicts = sisyphus.models.get_pages(offset=offset, limit=limit, key=key, cli=cli)
    page_dicts = [ sisyphus.models.convert_pub_date_to_datetime(x) for x in page_dicts ]
    total_pages = sisyphus.models.num_pages(key=key, cli=cli)
    per_page = 10
    pages = [ x for x in range(0, total_pages, per_page)]

    extra_modules = [(0.3, tags_module(limit=3, cli=cli))]
    context = {'pages': page_dicts,
               'pager_show': (len(page_dicts) >= per_page) or offset > per_page,
               'pager_offset': offset,
               'nav_tags': sisyphus.models.tags(limit=getattr(settings,'NUM_TAGS_NAV', 8), cli=cli),
               'pager_next': offset + per_page,
               'pager_prev': offset - per_page,
               'pager_remaining': offset + per_page < total_pages,
               'pager_pages': pages,
               'html_title': STORY_LIST_TITLES.get(title, TAG_LIST_TITLE % title),
               'modules': default_modules(None, extra_modules, limit=5, cli=cli),
               }
    return render_to_response('sisyphus/page_list.html', context, context_instance=RequestContext(request))

def tag_list(request, slug):
    "Retrieve stories within a tag."
    cli = sisyphus.models.redis_client()
    key = sisyphus.models.TAG_PAGES_ZSET_BY_TREND % slug
    return render_list(request, key, "/tags/%s/" % slug, slug, cli=cli)

def similar_list(request, slug, cli=None):
    "List of stories similar to this one."
    cli = sisyphus.models.redis_client()
    page = sisyphus.models.get_page(slug, cli=cli)
    key = sisyphus.models.ensure_similar_pages_key(page, cli=cli)
    return render_list(request, key, "/similar/%s/" % slug, "Similar to %s" % page['title'], cli=cli)

def story_list(request, list_type, cli=None):
    "Create a storylist page."
    if list_type in STORY_LIST_KEYS:
        key = STORY_LIST_KEYS[list_type]
        return render_list(request, key, "/list/%s/" % list_type, list_type, cli=cli)
    else:
        raise Http404


def page(request, slug):
    "Render a page."
    cli = sisyphus.models.redis_client()
    object = sisyphus.models.get_page(slug, cli=cli)
    if object:
        object = sisyphus.models.convert_pub_date_to_datetime(object)
        extra_modules = []
        if object['published']:
            sisyphus.models.track(request, object, cli=cli)
            before_mod, after_mod = context_module(object, cli=cli)
            extra_modules = [(0.7, similar_pages_module(object, cli=cli)),
                             (0.1, analytics_module(cli=cli)),
                             (0.71, before_mod),
                             (0.72, after_mod),
                             ]

        context = { 'page': object,
                    'domain': settings.DOMAIN,
                    'twitter_username': settings.TWITTER_USERNAME,
                    'nav_tags': sisyphus.models.tags(limit=getattr(settings,'NUM_TAGS_NAV', 8), cli=cli),
                    'modules': default_modules(object, extra_modules, cli=cli),
                    'disqus_shortname': settings.DISQUS_SHORTNAME,
                    }
        return render_to_response('sisyphus/page_detail.html', context, context_instance=RequestContext(request))
    else:
        raise Http404

def frontpage(request):
    "Render frontpage."
    return story_list(request, "recent")

def search(request):
    "Search against blog."
    cli = sisyphus.models.redis_client()
    pages = []
    query = ''
    if 'q' in request.GET:
        query = request.GET['q']
        search_resp = sisyphus.models.search(query, cli=cli)
        if search_resp:
            pages = [ sisyphus.models.convert_pub_date_to_datetime(x) for x in search_resp ]
    extra_modules = []
    context = { 'pages': pages,
                'query': query,
                'html_title': "%s pages match \"%s\"" % (len(pages), query),
                'nav_tags': sisyphus.models.tags(limit=getattr(settings,'NUM_TAGS_NAV', 8), cli=cli),
                'modules': default_modules(None, extra_modules, cli=cli),
                    }
    return render_to_response('sisyphus/search.html', context, context_instance=RequestContext(request))
