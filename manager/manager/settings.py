"""
Django settings for manager project.

Generated by 'django-admin startproject' using Django 3.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os

import environ

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
    ADMIN_ENABLED=(bool, True),
)
environ.Env.read_env()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")
ADMIN_ENABLED = env("ADMIN_ENABLED")

# Format example: '127.0.0.1'
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

AUTH_USER_MODEL = "backend.TaggUser"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 100,
}


# LOGGING
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "root": {"level": "INFO", "handlers": ["file"]},
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": env("LOG_FILE"),
            "formatter": "default",
        },
        "regenerate_socials": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "regenerate_socials.log",
            "formatter": "default",
        },
        "link_taggs_reminder": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "link_taggs_reminder.log",
            "formatter": "default",
        },
        "widget_view_boost": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "widget_view_boost.log",
            "formatter": "default",
        },
        "moments_posted_reminder": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "moments_posted_reminder.log",
            "formatter": "default",
        },
        "recommender_features": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "recommender_features.log",
            "formatter": "default",
        },
        "profile_visits": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "profile_visits.log",
            "formatter": "default",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": True,
        },
        "regenerate_socials": {
            "handlers": ["regenerate_socials"],
            "level": "INFO",
            "propagate": True,
        },
        "link_taggs_reminder": {
            "handlers": ["link_taggs_reminder"],
            "level": "INFO",
            "propagate": True,
        },
        "widget_view_boost": {
            "handlers": ["widget_view_boost"],
            "level": "INFO",
            "propagate": True,
        },
        "moments_posted_reminder": {
            "handlers": ["moments_posted_reminder"],
            "level": "INFO",
            "propagate": True,
        },
        "recommender_features": {
            "handlers": ["recommender_features"],
            "level": "INFO",
            "propagate": True,
        },
        "profile_visits": {
            "handlers": ["profile_visits"],
            "level": "INFO",
            "propagate": True,
        },
    },
    "formatters": {
        "default": {
            "format": (
                u"%(asctime)s [%(levelname)-6s] "
                "(%(module)s.%(funcName)s) %(message)s"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
}

if DEBUG:
    root = LOGGING["root"]
    handlers = LOGGING["handlers"]
    console = "console"
    root["handlers"].append(console)
    handlers[console] = {
        "level": "INFO",
        "class": "logging.StreamHandler",
        "formatter": "default",
    }

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "backend",
    "rest_framework.authtoken",
    "fcm_django",
    "django_crontab",
    "user_visit",
    "stream_chat",
    "background_task",
    "drf_yasg",
    "corsheaders",
    "rest_framework",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "user_visit.middleware.UserVisitMiddleware",
]

ROOT_URLCONF = "manager.urls"
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "manager.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    # "default": {
    #     "ENGINE": "django.db.backends.sqlite3",
    #     "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    # }
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "tagg_dev",
        "USER": "postgres",
        "PASSWORD": "dDFFZ2Aa2xk4",
        "HOST": "tagg-dev.cwrndgrpplhp.us-east-2.rds.amazonaws.com",
        "PORT": "5432",
    }
}

# https://medium.com/@netfluff/memcached-for-django-ecedcb74a06d
# https://docs.djangoproject.com/en/3.2/topics/cache/
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        "LOCATION": "127.0.0.1:11211",
    }
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://192.168.101.107:3000",
    "https://web.tagg.id",
]


# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_USE_TLS = env("EMAIL_USE_TLS")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_PORT = env("EMAIL_PORT")

# Twilio
TWILIO_ACCOUNT_SID = env("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = env("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = env("TWILIO_PHONE_NUMBER")


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True



# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = "/static/"

# S3
S3_BUCKET = env("S3_BUCKET")
S3_MOMENTS_FOLDER = env("S3_MOMENTS_FOLDER")
S3_WIDGETS_FOLDER = env("S3_WIDGETS_FOLDER")
S3_THUMBNAILS_FOLDER = env("S3_THUMBNAILS_FOLDER")
S3_PATH_ACCESS = env("S3_PATH_ACCESS")
S3_PATH_SECRET = env("S3_PATH_SECRET")
S3_VIDEO_BUCKET_URL = env("S3_VIDEO_BUCKET_URL")
S3_PRE_OBJECT_URI = env("S3_PRE_OBJECT_URI")
S3_SMALL_PROFILE_PIC_FOLDER = env("S3_SMALL_PROFILE_PIC_FOLDER")
S3_LARGE_PROFILE_PIC_FOLDER = env("S3_LARGE_PROFILE_PIC_FOLDER")
S3_SUGGESTED_PEOPLE_FOLDER = env("S3_SUGGESTED_PEOPLE_FOLDER")
S3_VIDEO_BUCKET = env("S3_VIDEO_BUCKET")
S3_VIDEO_QUEUE_BUCKET = env("S3_VIDEO_QUEUE_BUCKET")

# User agents
USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 8.0.0; SM-G960F Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.84 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Mobile/15E148 Safari/604.1",
]

# image settings
MAX_WIDTH = 580
MAX_HEIGHT = 580
RATIO_WIDTH = 1
RATIO_HEIGHT = 1

# suggested people image settings
# SP_HEIGHT = 812
# SP_WIDTH = 375
SP_RATIO = 0.46

# Social Media
OAUTH_REDIRECT_URI = env("REDIRECT_URI")
INSTAGRAM_APP_ID = env("IG_APP_ID")
INSTAGRAM_APP_SECRET = env("IG_APP_SECRET")
FACEBOOK_APP_ID = env("FB_APP_ID")
FACEBOOK_APP_SECRET = env("FB_APP_SECRET")
FACEBOOK_APP_ACCESS_ID = env("FB_APP_ACCESS_ID")
TWITTER_API_KEY = env("TWITTER_API_KEY")
TWITTER_API_SECRET = env("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = env("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = env("TWITTER_ACCESS_TOKEN_SECRET")

# Report
REPORT_RECIPIENT = env("REPORT_RECIPIENT")

"""
{
    "School": {
        "Category": [
            "Badge",
            ...
        ],
        ...
    },
    ...
}
"""

BADGE_LIMIT = 3

BADGES = {
    "art",
    "astronomy",
    "athlete",
    "author",
    "beauty",
    "blogger",
    "cars",
    "chess",
    "coffee",
    "college",
    "cooking",
    "dance",
    "diy",
    "dj",
    "design",
    "engineering",
    "entertainment",
    "entrepreneur",
    "fashion",
    "film",
    "finance",
    "fishing",
    "fitness",
    "food",
    "foreign_language",
    "gaming",
    "gardening",
    "health",
    "investing",
    "jewelry",
    "journalism",
    "legal",
    "marketing",
    "media",
    "medicine",
    "mental_health",
    "music",
    "nature",
    "news",
    "outdoor_activities",
    "philosophy",
    "podcast",
    "politics",
    "producer",
    "public_figure",
    "photography",
    "reading",
    "retail",
    "sports",
    "technology",
    "travel",
    "vegetarian",
    "video_production",
    "vintage",
    "volunteer_and_non_profit",
    "wine",
    "writing",
    "yoga",
}


DISCOVER_CATEGORIES = {
    "trending_on_tagg": ("Trending on Tagg", None),
    "brown_18": ("Brown '18", "Brown"),
    "brown_19": ("Brown '19", "Brown"),
    "brown_20": ("Brown '20", "Brown"),
    "brown_21": ("Brown '21", "Brown"),
    "brown_22": ("Brown '22", "Brown"),
    "brown_23": ("Brown '23", "Brown"),
    "brown_24": ("Brown '24", "Brown"),
    "cornell_18": ("Cornell '18", "Cornell"),
    "cornell_19": ("Cornell '19", "Cornell"),
    "cornell_20": ("Cornell '20", "Cornell"),
    "cornell_21": ("Cornell '21", "Cornell"),
    "cornell_22": ("Cornell '22", "Cornell"),
    "cornell_23": ("Cornell '23", "Cornell"),
    "cornell_24": ("Cornell '24", "Cornell"),
}

FCM_DJANGO_SETTINGS = {
    "FCM_SERVER_KEY": "AAAAEHXMOHo:APA91bFAIEnj7itjoY-vSxodOCjxb-HJpqks5qxtnBjYmYiPMra_QqiUTZKtFOB7A3KprRg_DoHJApFYUVoBXaAfLDWlKR1yEp_HBYmLv_qVMRv-HedOeor1YA86GAFfW8KNYp2GPv63",
    # true if you want to have only one active device per registered user at a time
    # default: False
    "ONE_DEVICE_PER_USER": True,
    # devices to which notifications cannot be sent,
    # are deleted upon receiving error response from FCM
    # default: False
    "DELETE_INACTIVE_DEVICES": False,
}

# Stream API: Chat
STREAM_API_KEY = env("STREAM_API_KEY")
STREAM_API_SECRET = env("STREAM_API_SECRET")

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "api_key": {"type": "apiKey", "in": "header", "name": "Authorization"}
    },
}
#*/5 * * * *
CRONJOBS = [
    # every day at 9 AM (server needs to be running for this to run successfully)
    ("0 9 * * *", "django.core.management.call_command", ["regenerate_fb_token"]),
    ("0 9 * * *", "django.core.management.call_command", ["regenerate_ig_token"]),
    # every day at 9 AM (server needs to be running for this to run successfully)
    ("0 9 * * *", "django.core.management.call_command", ["link_taggs_reminder"]),
    ("0 * * * *", "django.core.management.call_command", ["moments_posted_reminder"]),
    ("0 * * * *", "django.core.management.call_command", ["moment_posted_friend"]),
    ("0 5 * * *", "django.core.management.call_command", ["dailyMoments"]),
    (
        "0 * * * *",
        "django.core.management.call_command",
        ["process_tasks"],
        {"duration": 3000},
    ),
    ("0 */6 * * *", "django.core.management.call_command", ["update_recommender"]),
    ("0 */3 * * *", "django.core.management.call_command", ["profile_viewed"]),
    ("0 4,8,12,16,20 * * *", "django.core.management.call_command", ["widget_view_boost"]),
]

# Data Science
DS_ML_SERVICE = env("DS_ML_SERVICE")

# supports comma separated versions
LIVE_VERSION = "1.0" if DEBUG else env("LIVE_VERSION")
ENV = env("ENV")
