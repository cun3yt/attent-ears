# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_USER_MODEL = 'visualizer.User'

GOOGLE_OAUTH2_KEY = '415186092964-5l043esdprn1eg936ct7tnoi9rmtgidp.apps.googleusercontent.com'
GOOGLE_OAUTH2_SECRET = 'Y-KVRINYeqiA94x-BWepCvYX'
GOOGLE_TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = GOOGLE_OAUTH2_KEY
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = GOOGLE_OAUTH2_SECRET
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/contacts.readonly",
    "https://www.googleapis.com/auth/userinfo.profile",
]

SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS = {
    'access_type': 'offline',
    'approval_prompt': 'force'
}

SOCIAL_AUTH_USER_MODEL = 'visualizer.User'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/'
