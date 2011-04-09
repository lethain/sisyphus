from django.core.management.base import BaseCommand, CommandError
import sisyphus.models
import sisyphus.analytics
import django.http
import json
import time
import re

class Command(BaseCommand):
    args = "<file_to_load file_to_load ...>"
    help = "Load analytics from Nginx server data."
    log_pattern = re.compile(r"""(?P<ip>\d{0,3}\.\d{0,3}.\d{0,3}\.\d{0,3}).+?
\[(?P<datetime>[0-9]{2}\/[A-Za-z]+\/[0-9]{4}:[0-9]{2}:[0-9]{2}:[0-9]{2})
.{9}
(?P<method>GET|POST|CONNECT|HEAD) (?P<path>.*?) HTTP\/1.[0-9]{1}"
.{5}
\d+
.{1}
"(?P<refer>.*?)"
(?P<agent>.*)""", re.VERBOSE)
    date_format = "%d/%b/%Y:%H:%M:%S"
    ignore = ('/','/tags/','/favicon.ico/', '/feeds/')
    errors = []
    clean_keys = True #False

    def extract(self, line):
        matches = self.log_pattern.match(line)
        try:
            return {
                'ip':matches.group('ip'),
                'method': matches.group('method'),
                'ts': int(time.mktime(time.strptime(matches.group('datetime'), self.date_format))),
                'path': matches.group('path').strip(),
                'agent':matches.group('agent').strip()[1:-1],
                'refer': matches.group('refer').strip(),
                }
        except AttributeError:
            self.errors.append(line)

    def handle(self, *args, **kwargs):
        cli = sisyphus.models.redis_client()
        if self.clean_keys:
            keys = cli.keys("analytics.*")
            if keys:
                cli.delete(*keys)

        for file in args:
            print "Loading data from %s..." % (file,)
            start = time.time()
            i = 0
            valid = 0
            methods = {}
            entries = {}
            with open(file, 'r') as fin:
                for line in fin.readlines():
                    extracted = self.extract(line)
                    if extracted:
                        method = extracted['method']
                        methods[method] = methods.get(method, 0) + 1
                        if method == 'GET':
                            path = extracted['path']
                            if path.endswith('/') and path not in self.ignore and len(path.split('/')) == 3:
                                entries[path] = entries.get(path, 0) + 1
                                req = django.http.HttpRequest()
                                req.META['HTTP_REFERER'] = extracted['refer'] if extracted['refer'] != '-' else ""
                                req.META['REMOTE_ADDR'] = extracted['ip']
                                req.META['HTTP_USER_AGENT'] = extracted['agent']
                                page = { 'slug': path[1:-1] }
                                sisyphus.analytics.track(req, page, cli, extracted['ts'])
                                valid += 1

                    i += 1
            end = time.time()
            print methods
            print "Loading %s valid records of %s total records took %.2f seconds" % (valid, i, end-start)
