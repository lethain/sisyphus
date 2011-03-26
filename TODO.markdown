* fix trending
  * trending should be activity from last few hours or last day or osmething, not lifespan
  * the "by trend" score is still interesting for best of all time
  * store each page's hourly referrers and merge them together periodically
  * initially have text links in module (don't want to serve much JavaScript on normal page load)
  * have a per-post analysis page linked from module
* analytics
  * implement analytics module
  * implement analytics
  * top referrers for each article

* articles to write backwards compat
  * /articles/
  * /coding-projects/

* write article on blog explaining stuff
    * v3
    * trending
    * nginx rewrites for url backwards compatibility
    * social sharing
    * search
    * tags
    * similar content
    * more wiki-like
    * analytics
* deploy
    * change DNS to point lethain.com to new VPS
   
* import comments from irrational exuberance v2.0, only those more than 2 months old...


V2:

* use tidycss along with django-compress
* add mobile CSS

V100:
* add module pagination via ajax
* add facebook metadata (this is a pain, and I need images, and my facebook userid)