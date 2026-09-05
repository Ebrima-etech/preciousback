"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Debug environment variables
print(f'ENVIRONMENT={os.environ.get("ENVIRONMENT", "NOT SET")}', file=sys.stderr)
print(f'DEBUG={os.environ.get("DEBUG", "NOT SET")}', file=sys.stderr)
print(f'DATABASE_URL is set: {"DATABASE_URL" in os.environ}', file=sys.stderr)

from django.core.wsgi import get_wsgi_application
from django.conf import settings

print(f'IS_PRODUCTION={settings.IS_PRODUCTION}', file=sys.stderr)
print(f'Using database: {settings.DATABASES["default"].get("HOST", "N/A")}', file=sys.stderr)

application = get_wsgi_application()

# Run migrations on startup
if os.environ.get('DATABASE_URL'):
    try:
        from django.core.management import call_command
        print('Running migrations...', file=sys.stderr)
        call_command('migrate', '--noinput', verbosity=1)
        print('Migrations completed successfully', file=sys.stderr)
    except Exception as e:
        print(f'Migrations failed: {e}', file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
else:
    print('DATABASE_URL not set - skipping migrations', file=sys.stderr)
