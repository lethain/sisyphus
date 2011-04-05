import sisyphus.management.commands.update_markdown_page
import markdown
import json
import time

class Command(sisyphus.management.commands.update_markdown_page.Command):
    args = "<file_to_load file_to_load ...>"
    help = "Load or update Sisyphus drafts with Markdown content."

    def _override_page(self, page):
        "Override in subclasses for easy extension."
        page['html'] = markdown.markdown(page['html'], ['codehilite(css_class=highlight)', 'headerid','toc'])
        return page

    def handle(self, *args, **kwargs):
        kwargs['index'] = False
        return sisyphus.management.commands.update_markdown_page.Command.handle(self, *args, **kwargs)
