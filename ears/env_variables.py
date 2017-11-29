import os
""" Use `direnv` *nix package to load `.envrc` file's environment variables.
Load the env variables here to a python variable. Then use your py variable
in your code piece. This file is included in settings.py.
"""

# Environment

EARS_ENV = os.environ.get('EARS_ENV')
SECRET_KEY = os.environ.get('SECRET_KEY')

# Database Specs

## Product Database

EARS_PROD_DB_NAME = os.environ.get('EARS_PROD_DB_NAME')
EARS_PROD_DB_USER = os.environ.get('EARS_PROD_DB_USER')
EARS_PROD_DB_PASSWORD = os.environ.get('EARS_PROD_DB_PASSWORD')
EARS_PROD_DB_HOST = os.environ.get('EARS_PROD_DB_HOST')
EARS_PROD_DB_PORT = os.environ.get('EARS_PROD_DB_PORT')

## Warehouse
EARS_WAREHOUSE_DB_NAME = os.environ.get('EARS_WAREHOUSE_DB_NAME')
EARS_WAREHOUSE_DB_USER = os.environ.get('EARS_WAREHOUSE_DB_USER')
EARS_WAREHOUSE_DB_PASSWORD = os.environ.get('EARS_WAREHOUSE_DB_PASSWORD')
EARS_WAREHOUSE_DB_HOST = os.environ.get('EARS_WAREHOUSE_DB_HOST')
EARS_WAREHOUSE_DB_PORT = os.environ.get('EARS_WAREHOUSE_DB_PORT')

## Redis

RQ_DEFAULT_HOST = os.environ.get('RQ_DEFAULT_HOST')
RQ_DEFAULT_PORT = os.environ.get('RQ_DEFAULT_PORT')
RQ_DEFAULT_DB = os.environ.get('RQ_DEFAULT_DB')
RQ_DEFAULT_PASSWORD = os.environ.get('RQ_DEFAULT_PASSWORD')

# Integrations

## Outreach

OUTREACH_CLIENT_ID = os.environ.get('OUTREACH_CLIENT_ID')
OUTREACH_CLIENT_SECRET = os.environ.get('OUTREACH_CLIENT_SECRET')

## Google

GOOGLE_OAUTH2_KEY = os.environ.get('GOOGLE_OAUTH2_KEY')
GOOGLE_OAUTH2_SECRET = os.environ.get('GOOGLE_OAUTH2_SECRET')

## Salesforce

SALESFORCE_CONSUMER_KEY = os.environ.get('SALESFORCE_CONSUMER_KEY')
SALESFORCE_CONSUMER_SECRET = os.environ.get('SALESFORCE_CONSUMER_SECRET')

## Slack

### Attent Bot

SLACK_ATTENT_BOT_CLIENT_ID = os.environ.get('SLACK_ATTENT_BOT_CLIENT_ID')
SLACK_ATTENT_BOT_CLIENT_SECRET = os.environ.get('SLACK_ATTENT_BOT_CLIENT_SECRET')
SLACK_VERIFICATION_TOKEN = os.environ.get('SLACK_VERIFICATION_TOKEN')
