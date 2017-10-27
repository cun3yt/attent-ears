"""
Django settings for ears project.

Generated by 'django-admin startproject' using Django 1.11.3.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

from .auth_settings import *

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

EARS_ENV=os.environ.get('EARS_ENV')
SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = (EARS_ENV == 'dev')

ALLOWED_HOSTS = ['localhost', '*.herokuapp.com']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'apps.google_calendar',
    'social_django',
    'apps.api_connection',
    'apps.outreach',
    'apps.salesforce',
    'apps.visualizer',
    'apps.attent_calendar',
    'sslserver',
    'stringcase',
    'django.contrib.postgres',
    'psqlextra',
]

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ears.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'ears.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'psqlextra.backend',
        'NAME': os.environ.get('EARS_PROD_DB_NAME'),
        'USER': os.environ.get('EARS_PROD_DB_USER'),
        'PASSWORD': os.environ.get('EARS_PROD_DB_PASSWORD'),
        'HOST': os.environ.get('EARS_PROD_DB_HOST'),
        'PORT': os.environ.get('EARS_PROD_DB_PORT'),
    },
    'warehouse': {
        'ENGINE': 'django_redshift_backend',
        'NAME': os.environ.get('EARS_WAREHOUSE_DB_NAME'),
        'USER': os.environ.get('EARS_WAREHOUSE_DB_USER'),
        'PASSWORD': os.environ.get('EARS_WAREHOUSE_DB_PASSWORD'),
        'HOST': os.environ.get('EARS_WAREHOUSE_DB_HOST'),
        'PORT': os.environ.get('EARS_WAREHOUSE_DB_PORT'),
    },
}

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = 'static'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]
