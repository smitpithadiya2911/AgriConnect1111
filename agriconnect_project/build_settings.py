"""
Minimal settings for Vercel build (collectstatic only).
Overrides DATABASES to use SQLite so no MySQL driver is needed during build.
"""
from agriconnect_project.settings import *  # noqa

# Use in-memory SQLite — collectstatic doesn't need a real DB
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
