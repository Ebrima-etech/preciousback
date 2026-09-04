"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

# Run migrations and collect static files on startup if DATABASE_URL is available
if os.environ.get('DATABASE_URL'):
    try:
        from django.core.management import call_command
        call_command('migrate', '--noinput', verbosity=0)
        call_command('collectstatic', '--noinput', verbosity=0)
    except Exception as e:
        print(f'Startup tasks failed: {e}', file=sys.stderr)
        # Don't block startup if tasks fail
