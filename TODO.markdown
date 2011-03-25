* script for aggregating media and loading stories

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
  * /will-larson/
* django-compress for static media (far-future expires or death)
* sitemap.xml
* robots.txt
* write article on blog explaining stuff
    * v3
    * trending
    * nginx rewrites for url backwards compatibility
    * search
    * tags
    * similar content
    * more wiki-like
    * analytics
* deploy
    * add TWITTER_USERNAME to settings on dev.lethain.com
    * change DOMAIN to lethain.com
* import comments from irrational exuberance v2.0


V2:


* add mobile CSS
* add module pagination via ajax

V100:
* add facebook metadata (this is a pain, and I need images, and my facebook userid)