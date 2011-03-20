"Views for blog application."
from django.shortcuts import render_to_response
import sisyphus.models

# trending pages, recent pages, similar by tags

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
    return { 'title':'Analytics', 'html':html }

def storylist_module(key, title, more_link=None, limit=3, cli=None):
    cli = cli or sisyphus.models.redis_client()
    objects = sisyphus.models.get_pages(limit=limit, key=key, cli=cli)
    return { 'title': title, 'pages': objects, 'more_link': more_link }

def trending_module(limit=3, cli=None):
    "Create default trending module."
    return storylist_module(sisyphus.models.PAGE_ZSET_BY_TREND,
                            "Trending",
                            "/list/trending/")

def recent_module(limit=3, cli=None):
    "Create default trending module."
    return storylist_module(sisyphus.models.PAGE_ZSET_BY_TIME,
                            "Recent",
                            "/list/recent/")

def similar_pages_module(page, limit=3, cli=None):
    """
    Find stories which have a high overlap of tags with this one,
    then also sort by those articles' trending scores.
    """
    pages = sisyphus.models.similar_pages(page, limit=limit, cli=cli)
    if pages:
        return {'title': 'Similar', 'pages':pages, 'more_link':'/list/similar/%s' % page['slug']}
    else:
        return None
    

def add_module(cli=None):
    cli = cli or sisyphus.models.redis_client()
    objects = sisyphus.models.get_pages(cli=cli, limit=3)
    return { 'title': 'Trending',
             'pages': objects,
             'more_link': '/tags/',
             }

def page(request, slug):
    "Render a page."
    cli = sisyphus.models.redis_client()
    object = sisyphus.models.get_page(slug, cli=cli)
    object = sisyphus.models.convert_pub_date_to_datetime(object)

    modules = (about_module(cli=cli),
               trending_module(cli=cli),
               similar_pages_module(object, cli=cli),
               recent_module(cli=cli),
               analytics_module(cli=cli))
    active_modules = tuple(x for x in modules if x)

    context = { 'page': object,
                'modules': active_modules,
                }

    return render_to_response('sisyphus/page_detail.html', context)

def frontpage(request):
    "Render frontpage."
    cli = sisyphus.models.redis_client()
    objects = sisyphus.models.get_pages(cli=cli)
    objects = [ sisyphus.models.convert_pub_date_to_datetime(x) for x in objects ]
    total_objects = sisyphus.models.num_pages(cli=cli)

    offset = 0
    per_page = 10
    num_pages = total_objects / per_page
    start_page = offset / per_page
    pages = range(start_page, num_pages)[:10]

    context = {'pages': objects,
               'pager_is_not_first': offset != 0,
               'pager_is_not_end': start_page != num_pages,
               'pager_pages': pages,
               }
    
    return render_to_response('sisyphus/page_list.html', context)
