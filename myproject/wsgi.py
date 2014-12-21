import os
import sys
import django
from django.core.handlers.wsgi import WSGIHandler
sys.path.append('/home/joshyg/webapps/nflbacktest/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'myproject.settings'
#django.setup()

application = WSGIHandler()
