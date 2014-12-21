from django.conf.urls import patterns, include, url
from django.conf import settings


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'myproject.views.home', name='home'),
    # url(r'^myproject/', include('myproject.foo.urls')),
    url(r'^$', 'teamstats.views.main'),
    url(r'submit', 'teamstats.views.submit'),
    #from messageboard
    url(r'forum', 'posts.views.login_page'),
    url(r'^authenticate_user/$', 'posts.views.authenticate_user'),
    url(r'home/(?P<username>\S+)/account_settings', 'posts.views.account_settings'),
    url(r'^home/(?P<index>\d+)/$', 'posts.views.main'),
    url(r'^home/', 'posts.views.main'),
    url(r'(?P<post_id>\d+)/add_post/', 'posts.views.add_post'),
    url(r'post/(?P<post_id>\d+)/', 'posts.views.view_comments'),
    url(r'(?P<post_id>\d+)/add_comment/', 'posts.views.add_comment'),
    url(r'(?P<post_id>\d+)/vote/', 'posts.views.vote'),
    url(r'logout/$', 'posts.views.logout_user'),
    url(r'(?P<setting>\S+)/edit_settings/', 'posts.views.edit_settings'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    ##following required for serving photos/other media stored in files
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT,
    }),
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.STATIC_ROOT,
    }),
    
)
