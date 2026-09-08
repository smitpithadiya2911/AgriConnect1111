import os
import sys
import traceback
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

django_app = None
init_error = None

try:
    from django.core.wsgi import get_wsgi_application
    django_app = get_wsgi_application()
except Exception:
    init_error = traceback.format_exc()

def handler(environ, start_response):
    if init_error:
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'text/html; charset=utf-8')]
        start_response(status, headers)
        db_status = "SET" if os.environ.get("DATABASE_URL") else "NOT SET (Please configure DATABASE_URL in Vercel Project Settings)"
        html = f"""<!DOCTYPE html>
<html>
<head><title>AgriConnect - Initialization Error</title></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; background: #0f172a; color: #f8fafc; max-width: 900px; margin: 0 auto; line-height: 1.5;">
    <h1 style="color: #ef4444;">AgriConnect Backend Initialization Failed</h1>
    <p><b>DATABASE_URL in Environment:</b> {db_status}</p>
    <p>Django failed to start on Vercel Serverless. Full error traceback:</p>
    <pre style="background: #1e293b; padding: 18px; border-radius: 8px; color: #f87171; overflow-x: auto; white-space: pre-wrap;">{init_error}</pre>
</body>
</html>"""
        return [html.encode('utf-8')]

    try:
        return django_app(environ, start_response)
    except Exception:
        err = traceback.format_exc()
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'text/html; charset=utf-8')]
        start_response(status, headers)
        db_status = "SET" if os.environ.get("DATABASE_URL") else "NOT SET (Please configure DATABASE_URL in Vercel Project Settings)"
        html = f"""<!DOCTYPE html>
<html>
<head><title>AgriConnect - Runtime Error</title></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; background: #0f172a; color: #f8fafc; max-width: 900px; margin: 0 auto; line-height: 1.5;">
    <h1 style="color: #f59e0b;">AgriConnect Runtime Error</h1>
    <p><b>DATABASE_URL in Environment:</b> {db_status}</p>
    <p>An uncaught error occurred during request processing:</p>
    <pre style="background: #1e293b; padding: 18px; border-radius: 8px; color: #fca5a5; overflow-x: auto; white-space: pre-wrap;">{err}</pre>
</body>
</html>"""
        return [html.encode('utf-8')]

app = handler
application = handler
