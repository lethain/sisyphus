from django.core.management.base import BaseCommand, CommandError
import sisyphus.models
import json
import time

class Command(BaseCommand):
    args = "<file_to_load file_to_load ...>"
    help = "Load or update Sisyphus pages."

    def _override_page(self, page):
        "Override in subclasses for easy extension."
        return page
    
    def handle(self, *args, **options):
        for file in args:
            with open(file, 'r') as fin:
                meta = ["{"]
                html = []        
                ended = False
                for line in fin.readlines():
                    if not ended and len(line.strip()) == 0:
                        ended = True
                    elif ended:
                        html.append(line.rstrip().decode('utf-8'))
                    else:
                        meta.append(line.rstrip())
                meta[-1] = meta[-1].rstrip(',')
                meta.append("}")
                try:
                    page = json.loads(u"\n".join(meta))
                except Exception, e:
                    print meta
                    raise

                if 'pub_date' not in page:
                    page['pub_date'] = int(time.time())
                if 'tags' not in page:
                    page['tags'] = []

                page['html'] = u"\n".join(html)
                sisyphus.models.add_page(self._override_page(page))


