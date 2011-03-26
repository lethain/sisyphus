* django-compress for static media (far-future expires or death)
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
  * /will-larson/ publish date should be my birthday in 1985
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
    * change DOMAIN to lethain.com
    * change DNS to point lethain.com to new VPS
   
* import comments from irrational exuberance v2.0


V2:


* add mobile CSS
* add module pagination via ajax

V100:
* add facebook metadata (this is a pain, and I need images, and my facebook userid)