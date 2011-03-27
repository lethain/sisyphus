* analytics
  * product
    * site overview
      * lifetime refers
      * lifetime traffic per post
      * recent traffic per post
    * page analytics
      * lifetime traffic per referrer
      * recent traffic per referrer
      * traffic per hour for last 24 hours
      * 
    * analytics module
      * top 3 referers for this post
      * link to see all analytics data
  * implementation
    * refer.SLUG - zset with refer domain as slug
    * refer.MONTH - monthly zset with refer domain as slug
    * 
  * notes
    * nofollow links on the refers


* analytics/trending
  * trending should be activity from last few hours or last day or osmething, not lifespan
  * the "by trend" score is still interesting for best of all time
  * store each page's hourly referrers and merge them together periodically
  * initially have text links in module (don't want to serve much JavaScript on normal page load)
  * have a per-post analysis page linked from module
  * implement analytics module
  * implement analytics
  * top referrers for each article
* articles to write backwards compat
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