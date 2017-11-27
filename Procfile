release: bash ./scripts/heroku_deploy.sh
web: gunicorn ears.wsgi --log-file -
worker: ./manage.py rqworker default
