import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-...'  # generate your own
DEBUG = True
ALLOWED_HOSTS = []

X_FRAME_OPTIONS = 'SAMEORIGIN'
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pages',  # our app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ai_search_project.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'ai_search_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'pages' / 'static']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Solr configuration
SOLR_URL = 'http://10.4.0.5:8983/solr/ai_law/query'
SOLR_ROWS = 5
# print( "_____ SETTTINSGS --> SOLR_URL", SOLR_URL )
OLLAMA_URL = 'http://10.5.0.5:11434/api/embed'
OLLAMA_EMBED_MODEL = 'qwen3-embedding:0.6b'
OLLAMA_CHATBOT_MODEL = 'FableForge-AI/nexus-legal'

# Product dataset
PRODUCT_DATA_FILE = 'data/product.csv'

