import os
import sys
print os.path.abspath(__file__)
if ( os.path.abspath(__file__).find('nflbacktest_dev') == -1 ):
    import django
    from django.core.handlers.wsgi import WSGIHandler
    sys.path.append('/home/joshyg/webapps/nflbacktest/')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'myproject.settings'
    application = WSGIHandler()
else:
    sys.path.append('/home/joshyg/webapps/nflbacktest_dev/')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'myproject.settings'

    from django.core.wsgi import get_wsgi_application

    application = get_wsgi_application()
