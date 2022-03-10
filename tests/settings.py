import os

MODELCLUSTER_ROOT = os.path.dirname(os.path.dirname(__file__))
MEDIA_ROOT = os.path.join(MODELCLUSTER_ROOT, 'test-media')

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DATABASE_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DATABASE_NAME', 'modelcluster'),
        'USER': os.environ.get('DATABASE_USER', None),
        'PASSWORD': os.environ.get('DATABASE_PASS', None),
        'HOST': os.environ.get('DATABASE_HOST', None),
    }
}

SECRET_KEY = 'not needed'

INSTALLED_APPS = [
    'modelcluster',

    'django.contrib.contenttypes',
    'taggit',

    'tests',
]

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

USE_TZ = True
TIME_ZONE = 'America/Chicago'
ROOT_URLCONF = 'tests.urls'
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
