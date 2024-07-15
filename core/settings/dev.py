from .common import *  # noqa

DEBUG = True
NO_RELOAD = False

INSTALLED_APPS += [
    "anymail",
    "django_browser_reload",
    "django_extensions",
]

MIDDLEWARE += [
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = []

# DJANGO-DEBUG-TOOLBAR
INTERNAL_IPS = [
    "127.0.0.1",
]

# DJANGO_ANYMAIL
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
DEFAULT_FROM_EMAIL = "info@mg.webbografico.com"

ANYMAIL = {
    "MAILGUN_API_KEY": env("MAILGUN_API_KEY"),
    "MAILGUN_API_URL": env("MAILGUN_API_URL"),
    "MAILGUN_SENDER_DOMAIN": env("MAILGUN_SENDER_DOMAIN"),
}

# DJANGO_ALLAUTH
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
