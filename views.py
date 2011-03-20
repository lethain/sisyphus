"Views for blog application."
from django.shortcuts import render_to_response
import sisyphus.models

def page(request, slug):
    "Render a page."
    cli = sisyphus.models.redis_client()
    object = sisyphus.models.get_page(slug, cli=cli)
    object = sisyphus.models.convert_pub_date_to_datetime(object)
    context = { 'page': object }
    print context

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
