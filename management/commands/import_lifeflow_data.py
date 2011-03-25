from django.core.management.base import BaseCommand, CommandError
import sisyphus.models
from django.conf import settings
import json
import time
import datetime
import os.path

class Command(BaseCommand):
    args = "<blog_root_directory json_db_dump_to_load json_db_dump_to_load ...>"
    help = "Create Sisyphus pages from a LifeFlow export."

    def handle(self, *args, **options):
        blog_root = args[0]
        draft_dir = os.path.join(blog_root, "draft")
        for file in args[1:]:
            with open(file, 'r') as fin:
                data = json.loads(fin.read())
                models = {}
                for entity in data:
                    model_type = entity['model']
                    model_set = models.get(model_type, [])
                    model_set.append(entity)
                    models[model_type] = model_set

                reverse_tag_lookup = {}
                for tag in models.get('lifeflow.tag',[]):
                    sisyphus.models.add_tag(tag['fields']['slug'], tag['pk'])
                    reverse_tag_lookup[tag['pk']] = tag['fields']['slug']

                for post in models.get('lifeflow.entry', []):
                    fields = post['fields']
                    tags = [ reverse_tag_lookup[x] for x in fields['tags'] ]
                    data = { 'title': fields['title'],
                             'slug': fields['slug'],
                             'tags': tags,
                             'pub_date': int(time.mktime(datetime.datetime.strptime(fields['pub_date'],"%Y-%m-%d %H:%M:%S").timetuple())),
                             'summary': fields['summary'].replace('\n',''),
                             'html': fields['body_html'].replace('/media/lifeflow/', settings.SISYPHUS_BLOG_STATIC_URL),
                             }
                    file_path = os.path.join(draft_dir, "%s.html" % (data['slug']))
                    print file_path
                    with open(file_path, 'w') as fout:
                        for key,val in data.iteritems():
                            if key is not 'html':
                                fout.write(u'%s: %s,\n' % (json.dumps(key),json.dumps(val)))
                        fout.write("\n")
                        fout.write(data['html'].encode('utf-8'))
                                         
                    

                
