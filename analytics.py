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
import datetime
import urlparse
from django.conf import settings


ANALYTICS_BACKOFF = "analytics.backoff.%s.%s"
ANALYTICS_REFER = "analytics.refer"
ANALYTICS_REFER_PAGE = "analytics.refer.%s"
ANALYTICS_USERAGENT = "analytics.useragent"
ANALYTICS_PAGEVIEW = "analytics.pv"
ANALYTICS_PAGEVIEW_BUCKET = "analytics.pv_bucket"
ANALYTICS_PAGEVIEW_PAGE_BUCKET = "analytics.pv_bucket.%s"
HISTORICAL_REFERRER = "imported from Google Analytics"
BOT_AGENTS = ("-",
              "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
              "Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)",
              "Disqus/1.0",
              "Sogou web spider/4.0(+http://www.sogou.com/docs/help/webmasters.htm#07)",
              "Baiduspider+(+http://www.baidu.com/search/spider.htm)",
              "Baiduspider+(+http://www.baidu.jp/spider/)",
              "ichiro/4.0 (http://help.goo.ne.jp/door/crawler.html)",
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

def page_analytics(page, cli=None, now=None):
    slug = page['slug']
    now = now or int(time.time())
    pipeline = cli.pipeline()
    pipeline.zrevrangebyscore(ANALYTICS_REFER_PAGE % slug, "+inf",
                              settings.MIN_PAGE_REF_PV,
                              start=0, 
                              num=settings.MAX_ANALYTICS_RESULTS,
                              withscores=True)
    pipeline.zscore(ANALYTICS_PAGEVIEW, slug)
    
    day_bucket = now / (24 * 60 * 60)
    bucket_keys = range(day_bucket, day_bucket-settings.ANALYTICS_SITE_DAYS_BACK, -1)
    pageview_page_bucket_key = ANALYTICS_PAGEVIEW_PAGE_BUCKET % slug
    for bucket_key in bucket_keys:
        pipeline.zscore(pageview_page_bucket_key, bucket_key)
    results = pipeline.execute()

    return {'views':int(results[1]),
            'referrers': [(x,int(y)) for x,y in results[0]],
            'avg_daily_views': results[1] / (datetime.datetime.today() - page['pub_date']).days,
            'recent_days': [(datetime.datetime.fromtimestamp(x*(60*60*24)), int(y)) for x,y in zip(bucket_keys, results[2:]) if y],
            }

def site_analytics(cli=None, now=None):
    now = now or int(time.time())
    pipeline = cli.pipeline()
    pipeline.zrevrangebyscore(ANALYTICS_REFER, "+inf", settings.MIN_PAGE_REF_PV, start=0, num=settings.MAX_ANALYTICS_RESULTS, withscores=True)
    pipeline.zrevrangebyscore(ANALYTICS_PAGEVIEW, "+inf", settings.MIN_PAGE_PV, start=0, num=settings.MAX_ANALYTICS_RESULTS, withscores=True)
    pipeline.zrevrangebyscore(ANALYTICS_USERAGENT, "+inf", settings.MIN_USERAGENT, start=0, num=settings.MAX_ANALYTICS_RESULTS, withscores=True)
    
    day_bucket = now / (24 * 60 * 60)
    bucket_keys = range(day_bucket, day_bucket-settings.ANALYTICS_SITE_DAYS_BACK, -1)
    for bucket_key in bucket_keys:
        pipeline.zscore(ANALYTICS_PAGEVIEW_BUCKET, bucket_key)

    results = pipeline.execute()
    return { 'pageviews': [(x, int(y)) for x,y in results[1]],
             'referrers': [(x, int(y)) for x,y in results[0]],
             'useragents': [(x, int(y)) for x,y in results[2]],
             'recent_days': [(datetime.datetime.fromtimestamp(x*(60*60*24)), int(y)) for x,y in zip(bucket_keys, results[3:]) if y],
             }

def track(request, page, cli, now=None):
    now = now or int(time.time())
    slug = page['slug']
    useragent = request.META['HTTP_USER_AGENT']
    lowered = useragent.lower()
    if not slug.endswith('.png') and \
            useragent not in BOT_AGENTS and \
            'subscribers' not in lowered and \
            'bot' not in lowered and \
            not useragent.startswith('Reeder'):
        refer = standardize_refer(request)
        ip = "X-Real-IP" # if proxied
        ip = request.META.get("X-Real-IP", request.META.get("REMOTE_ADDR", "127.0.0.1"))
        day_bucket = now / (24 * 60 * 60)
        hour_bucket = now / (60 * 60)
        min_bucket = now / 60
    
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

            # update time bucket analytics
            pipeline.zincrby(ANALYTICS_PAGEVIEW_BUCKET, day_bucket, 1)
            pipeline.zincrby(ANALYTICS_PAGEVIEW_PAGE_BUCKET % slug, day_bucket, 1)

            # buckets for users

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
