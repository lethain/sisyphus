from django.contrib.sitemaps import Sitemap
import sisyphus.models
import datetime

SITEMAPS = {}

class PageSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5

    def items(self):
        cli = sisyphus.models.redis_client()
        pages =  sisyphus.models.get_pages(limit=10000, cli=cli)
        return [ sisyphus.models.convert_pub_date_to_datetime(x) for x in pages ]

    def location(self, obj):
        return "/%s/" % (obj['slug'])

    def lastmod(self, obj):
        return obj.get('edit_date', obj.get('pub_date', datetime.datetime.now()))
SITEMAPS['pages'] = PageSitemap

class TagSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5
    lastmod = datetime.datetime.now()

    def items(self):
        cli = sisyphus.models.redis_client()
        return sisyphus.models.tags(limit=1000, withscores=False, cli=cli)

    def location(self, obj):
        return "/tags/%s/" % (obj,)

SITEMAPS['tags'] = TagSitemap
