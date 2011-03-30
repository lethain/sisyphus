"""
Can be run using:

    python ../../../local-sisyphus/blog/manage.py import_comments ~/git/irrational_exuberance/backup/irrational_exuberance_v2.json 

"""
from django.core.management.base import BaseCommand, CommandError
import sisyphus.models
from django.conf import settings
import json
import time
import datetime
import os.path

class Command(BaseCommand):
    args = "<json_db_dump_to_load json_db_dump_to_load ...>"
    help = "Load comments into Disqus from a LifeFlow export."
    stopwords = ("mortgage","cell", "handbag","sale","bags","store", "outlet", "gun", "mobile phone", "essay", 
                 "lawsuit", "nurse", "pharmacy", "attorney", "tax", "reseller", "dress",
                 "kreditkort", "penis", "bankrupt", "benzene", "juicy", "cheap", "credit",
                 "bonds", "bicycles", "painter", "rent", "flowers","gold", "watches",
                 "pittsburgh", "limo", "home security", "anonymous", "business continuity",
                 "nike shox", "las vegas", "san diego", "enterprise ip", "bachelors", "locator", "discount",
                 "weed","water damage","casino","dentist", "izlanda", "laser eye","cash",
                 "class action","weight loss", "nike", "video production","plumber",
                 "clearance", "oil", "forex","angies","iaq source", "hotel","resort","autotransport",
                 "girls","cigarette","loan","recovery","diease", "waste", "fha rates", "venice", "urgent",
                 "pasadena", "targeted","bingo","gifts", "smoking", "pregnancy", "reparo", "doctors",
                 "hollywood", "po box", "houston","wedding", "nba", "jerseys", "1080p",
                 "iphone monitoring", "belote", "artthopod", "mixed wrestling", "formula 21",
                 "iron doors", "ossf", "education degree","collection software", "high availability",
                 "phentermine", "scraps para",
                 )

    def filter(self, comment):
        txt = ("%s %s %s" % (comment['name'], comment['email'], comment['body'])).lower()
        for stop in self.stopwords:
            if stop in txt:
                return False

        if len(comment['body']) < 100:
            return False

        if comment['name'].startswith('www') or comment['name'].endswith('com'):
            return False

        return True

    def handle(self, *args, **options):
        print args
        for file in args:
            with open(file, 'r') as fin:
                data = json.loads(fin.read())

                comments = [ x['fields'] for x in data if x['model'] == "lifeflow.comment" ]
                pre_filter = reversed(comments)
                post_filter = [ x for x in pre_filter if self.filter(x) ]
                for f in post_filter:
                    print "%s (%s): %s" % (f['name'],  f['email'], f['body'][:10].replace("\n", " "))
                print "pre %s, post %s" % (len(comments), len(post_filter))
