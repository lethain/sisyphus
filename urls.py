from django.conf.urls.defaults import *
import sisyphus.sitemap

urlpatterns = patterns('',
    (r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sisyphus.sitemap.SITEMAPS}),
    (r'^search/$', 'sisyphus.views.search'),
    (r'^feeds/tag/(?P<tag_slug>.*)$', 'sisyphus.views.tag_feed'),
    (r'^feeds/(?P<feed_url>.*)$', 'sisyphus.views.feed'),
    (r'^tags/(?P<slug>[a-zA-Z0-9\-_]+)/$', 'sisyphus.views.tag_list'),
    (r'^tags/$', 'sisyphus.views.tags_list'),
    (r'^similar/(?P<slug>.+?)/$', 'sisyphus.views.similar_list'),
    (r'^list/(?P<list_type>[a-z]+)/$', 'sisyphus.views.story_list'),
    (r'^$', 'sisyphus.views.frontpage'),
    (r'^analytics/$', 'sisyphus.views.analytics'),
    (r'^analytics/(?P<slug>.+?)/$', 'sisyphus.views.page_analytics'),
    (r'^(?P<slug>.+?)/$', 'sisyphus.views.page'),
)
