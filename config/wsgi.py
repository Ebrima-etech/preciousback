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

print(f'DATABASE_URL is set: {"DATABASE_URL" in os.environ}', file=sys.stderr)
if os.environ.get('DATABASE_URL'):
    db_url = os.environ.get('DATABASE_URL')
    print(f'DATABASE_URL length: {len(db_url)} chars', file=sys.stderr)

application = get_wsgi_application()

# Run migrations and collect static files on startup if DATABASE_URL is available
if os.environ.get('DATABASE_URL'):
    try:
        from django.core.management import call_command
        call_command('migrate', '--noinput', verbosity=1)
        call_command('collectstatic', '--noinput', verbosity=1)
        print('Startup tasks completed successfully', file=sys.stderr)
    except Exception as e:
        print(f'Startup tasks failed: {e}', file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
else:
    print('DATABASE_URL not set - migrations will not run', file=sys.stderr)
