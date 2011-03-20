from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'(?P<slug>[a-zA-Z0-9\-_]+)/$', 'sisyphus.views.page'),
    (r'$', 'sisyphus.views.frontpage'),
)
