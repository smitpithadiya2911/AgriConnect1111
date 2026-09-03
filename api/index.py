import os
import sys
from pathlib import Path

# Add project root to sys.path so Django can import apps
current_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(current_dir))

# Patch MySQLdb with PyMySQL BEFORE Django loads any database backends
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agriconnect_project.settings')

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()
handler = app
application = app
