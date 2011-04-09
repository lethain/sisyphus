"""
Manage analytics data for Sisyphus.
The goal of this analytics system is
to facilitate exploring each individual
page's popularity and referers, not
really at understanding pages within
relation to each other.

Said another way, the goal is to
learn about how your posts do or do not
succeed. It's a page analysis tool, no
more and no less.

Track this data:

* refer per post

"""
import time
import urlparse
from django.conf import settings

ANALYTICS_BACKOFF = "analytics.backoff.%s.%s"
ANALYTICS_REFER = "analytics.refer"
ANALYTICS_REFER_PAGE = "analytics.refer.%s"
ANALYTICS_USERAGENT = "analytics.useragent"
ANALYTICS_PAGEVIEW = "analytics.pv"
ANALYTICS_PAGEVIEW_QTY = "analytics.pv_qty.%s"
ANALYTICS_PAGEVIEW_BUCKET = "analytics.pv_bucket.%s"
BOT_AGENTS = ("-",
              "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
              "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
              "Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)",
              "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
              "msnbot/2.0b (+http://search.msn.com/msnbot.htm)._",
              "Disqus/1.0",
              "Sogou web spider/4.0(+http://www.sogou.com/docs/help/webmasters.htm#07)",
              "Baiduspider+(+http://www.baidu.com/search/spider.htm)",
              "Baiduspider+(+http://www.baidu.jp/spider/)",
              "ichiro/4.0 (http://help.goo.ne.jp/door/crawler.html)",
              "MLBot (www.metadatalabs.com/mlbot)",
              "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
              "Mozilla/5.0 (compatible; MSIE 6.0b; Windows NT 5.0) Gecko/2009011913 Firefox/3.0.6 TweetmemeBot",
              "Mozilla/5.0 (compatible; Birubot/1.0) Gecko/2009032608 Firefox/3.0.8",
              "SAMSUNG-SGH-E250/1.0 Profile/MIDP-2.0 Configuration/CLDC-1.1 UP.Browser/6.2.3.3.c.1.101 (GUI) MMP/2.0 (compatible; Googlebot-Mobile/2.1; +http://www.google.com/bot.html)",
              "msnbot-media/1.1 (+http://search.msn.com/msnbot.htm)",
              "Java/1.6.0_24",
              "Python-urllib/2.6",
              )

def standardize_refer(request):
    url = request.META.get('HTTP_REFERER', '')
    parts = urlparse.urlparse(url)    
    standard = parts.netloc
    if standard.startswith("www.google"):
        standard = "www.google.com"

    return standard or "DIRECT"

def page_analytics(slug, limit=100, cli=None):
    pipeline = cli.pipeline()
    pipeline.zrevrangebyscore(ANALYTICS_REFER_PAGE % slug, "+inf",
                              settings.MIN_PAGE_REF_PV,
                              start=0, num=limit, withscores=True)
    pipeline.zscore(ANALYTICS_PAGEVIEW, slug)
    referrers, pageviews = pipeline.execute() 
    return {'views':pageviews,
            'referrers': [(x,int(y)) for x,y in referrers],
            }

def site_analytics(cli=None):
    pipeline = cli.pipeline()
    pipeline.zrevrangebyscore(ANALYTICS_REFER, "+inf", settings.MIN_PAGE_REF_PV, start=0, num=50, withscores=True)
    pipeline.zrevrangebyscore(ANALYTICS_PAGEVIEW, "+inf", settings.MIN_PAGE_PV, start=0, num=50, withscores=True)
    pipeline.zrevrangebyscore(ANALYTICS_USERAGENT, "+inf", settings.MIN_PAGE_PV, start=0, num=50, withscores=True)
    referrers, pageviews, useragents = pipeline.execute()
    return { 'pageviews': [(x, int(y)) for x,y in pageviews],
             'referrers': [(x, int(y)) for x,y in referrers],
             'useragents': [(x, int(y)) for x,y in useragents],
             }

def track(request, page, cli, now=None):
    now = now or int(time.time())
    slug = page['slug']
    useragent = request.META['HTTP_USER_AGENT']
    if not slug.endswith('.pngg') and useragent not in BOT_AGENTS and 'subscribers' not in useragent and not useragent.startswith('Reeder'):
        refer = standardize_refer(request)
        ip = "X-Real-IP" # if proxied
        ip = request.META.get("X-Real-IP", request.META.get("REMOTE_ADDR", "127.0.0.1"))
        hour_bucket = now / (60 * 60)
        min_bucket = now / (60 * 60)
    
        backoff_key = ANALYTICS_BACKOFF % (ip, min_bucket)
        cli.watch(backoff_key)
        should_track = not cli.exists(backoff_key)
        if should_track:
            pipeline = cli.pipeline()

            # update referer analytics
            pipeline.zincrby(ANALYTICS_REFER, refer, 1)
            pipeline.zincrby(ANALYTICS_REFER_PAGE % slug, refer, 1)

            # update all-time pageview analytics
            pipeline.zincrby(ANALYTICS_PAGEVIEW, slug, 1)

            # update user-agents
            pipeline.zincrby(ANALYTICS_USERAGENT, useragent, 1)

            # update pageview analytics for last N hours
            #ANALYTICS_PAGEVIEW_QTY = "analytics.pv_qty.%s"
            #ANALYTICS_PAGEVIEW_BUCKET = "analytics.pv_bucket.%s"
            #cli.zincrby(ANALYTICS_PAGEVIEW_BUCKET % slug, timebucket(), 1)

            # only record one action per IP per minute
            pipeline.set(backoff_key, 1)
            pipeline.expire(backoff_key, 60)
            try:
                pipeline.execute()
            except redis.exceptions.WatchError:
                # another request already got in
                # for this timebox for this IP
                pass
        else:
            cli.unwatch()
