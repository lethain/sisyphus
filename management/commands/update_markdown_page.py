import sisyphus.management.commands.update_page
import markdown
import json
import time

class Command(sisyphus.management.commands.update_page.Command):
    args = "<file_to_load file_to_load ...>"
    help = "Load or update Sisyphus pages with Markdown content."

    def _override_page(self, page):
        "Override in subclasses for easy extension."
        page['html'] = markdown.markdown(page['html'], ['codehilite(css_class=highlight)'])
        return page
