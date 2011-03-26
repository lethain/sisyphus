from django.core.management.base import BaseCommand, CommandError
import sisyphus.models
import sisyphus.management.commands.update_page
import sisyphus.management.commands.update_markdown_page
import json
import time
import os.path
import os

class Command(BaseCommand):
    args = "<root_sisyphus_content_dir>"
    help = "Synchronize a Sisyphus deployment with the contents of a Sisyphus content repository."

    def load_page(self, path, index=True):
        "Load a file."
        if path.endswith('.html'):
            sisyphus.management.commands.update_page.Command().handle(path, index=index)
        elif path.endswith('.markdown') or path.endswith('.md'):
            sisyphus.management.commands.update_markdown_page.Command().handle(path, index=index)
        else:
            print "Unknown extension: %s" % (path.split(".")[-1],)
    
    def handle(self, git_dir, **options):
        """
        for file in args:
            with open(file, 'r') as fin:
                pass
        """
        edit_dir = os.path.join(git_dir, "edit")
        print "Update edit pages in '%s'" % (edit_dir,)
        try:
            for file in os.listdir(edit_dir):
                filepath = os.path.join(edit_dir, file)
                self.load_page(filepath, index=False)
        except OSError:
            print "Missing %s" % edit_dir

        publish_dir = os.path.join(git_dir, "publish")
        print "Update publish pages in '%s'" % (publish_dir,)
        try:
            for file in os.listdir(publish_dir):
                filepath = os.path.join(publish_dir, file)
                self.load_page(filepath, index=True)
        except OSError:
            print "Missing %s" % publish_dir

