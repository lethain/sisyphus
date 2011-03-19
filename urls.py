from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'$', 'sisyphus.views.frontpage'),
)
