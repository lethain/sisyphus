from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^search/$', 'sisyphus.views.search'),
    (r'^feeds/(?P<feed_url>.*)$', 'sisyphus.views.feed'),
    (r'^tag/(?P<slug>[a-zA-Z0-9\-_]+)/$', 'sisyphus.views.tag_list'),
    (r'^tags/$', 'sisyphus.views.tags_list'),
    (r'^similar/(?P<slug>.+?)/$', 'sisyphus.views.similar_list'),
    (r'^list/(?P<list_type>[a-z]+)/$', 'sisyphus.views.story_list'),
    (r'^$', 'sisyphus.views.frontpage'),
    (r'^(?P<slug>.+?)/$', 'sisyphus.views.page'),
)
