import json
import sys
import sisyphus.models
import datetime
import time

raw_data = sys.stdin.read()
data = json.loads(raw_data)

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
             'summary': fields['summary'],
             'html': fields['body_html'],
             }
    sisyphus.models.add_page(data)


