web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --worker-class sync --timeout 60 --log-level info
release: python manage.py migrate && python manage.py collectstatic --noinput
