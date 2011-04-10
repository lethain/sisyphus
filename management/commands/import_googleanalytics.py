from django.core.management.base import BaseCommand, CommandError
import sisyphus.models
import sisyphus.analytics
import django.http
import json
import time
import re


class Command(BaseCommand):
    args = "<file_to_load file_to_load ...>"
    help = "Load analytics from Google Analytics Top Content report in CSV format."
    clean_keys = False

    def parse_day(self, day):
        # "Saturday, March 10, 2007",0
        date, pv = day.split('",')
        ts = int(time.mktime(time.strptime(date[1:], "%A, %B %d, %Y")))
        return ts, int(pv.strip().replace(',','').replace('"',""))

    def parse_url(self, url):
        # /entry/2008/jul/12/polishing-up-our-django-boss-search-service/,64965,62184,77.61242753623188,0.5748977339133823,0.575155853151697,0.0
        path, views, unique_views, avg_time, bounce, exit, rev  = url.split(',')
        path_parts = path.split('/')
        if path.startswith('/entry/') and len(path_parts) == 7:
            return { 'path': path, 'slug':path_parts[-2], 'views':views, 'unique_views': unique_views }

    def handle(self, *args, **kwargs):
        cli = sisyphus.models.redis_client()
        
        if self.clean_keys:
            keys = cli.keys("analytics.*")
            if keys:
                cli.delete(*keys)

        for file in args:
            print "Loading data from %s..." % (file,)
            with open(file) as fin:
                days = []
                urls = []
                in_days = False
                in_urls = False
                for line in fin.readlines():
                    if line.strip().startswith("#") or line.strip() == '':
                        in_days = False
                        in_urls = False
                    elif line.strip() == "Day,Pageviews":
                        in_days = True
                        in_urls = False
                    elif line.strip() == "Page,Pageviews,Unique Pageviews,Avg. Time on Page,Bounce Rate,% Exit,$ Index":
                        in_urls = True
                        in_days = False
                    elif in_days:
                        days.append(line)
                    elif in_urls:
                        urls.append(line)
                for day in days:
                    ts, pv = self.parse_day(day)
                    day_bucket = ts / (60 * 60 * 24)
                    cli.zincrby(sisyphus.analytics.ANALYTICS_PAGEVIEW_BUCKET, day_bucket, pv)
                    
                for url in urls:
                    url_data = self.parse_url(url)
                    if url_data:
                        cli.zincrby(sisyphus.analytics.ANALYTICS_PAGEVIEW, url_data['slug'], url_data['views'])
                        cli.zincrby(sisyphus.analytics.ANALYTICS_REFER, 
                                     sisyphus.analytics.HISTORICAL_REFERRER,
                                     url_data['views'])
                        cli.zincrby(sisyphus.analytics.ANALYTICS_REFER_PAGE % url_data['slug'],
                                     sisyphus.analytics.HISTORICAL_REFERRER,
                                     url_data['views'])

                        print url_data

                print "%s days, %s urls" % (len(days), len(urls))
