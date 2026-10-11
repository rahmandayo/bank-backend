import os
from dotenv import load_dotenv
# Import the package that converts DATABASE_URL into Django database configuration.
import dj_database_url

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'. Define the absolute path to the Django project root.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load the environment variables stored in the project's .env file.
load_dotenv(BASE_DIR / ".env")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/

# # SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-%8=u7xr8tn2#($%(_@6#tdww*-hh3@%bz=^1kbsr$y=fo@!lkg'

# Load the Django secret key from the environment.
SECRET_KEY = os.getenv("SECRET_KEY")

# Stop startup if the required secret key is missing.
if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be configured in the environment.")


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# FRONTEND CONNECTION SETTINGS STARTS
# Permit local development requests to reach Django.
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Allow React's local origin to read permitted cross-origin API responses.
CORS_ALLOWED_ORIGINS = ["http://localhost:8080"]

# Permit cookies on browser requests from the configured CORS origin.
CORS_ALLOW_CREDENTIALS = True

# Trust the React origin for Django's CSRF checks.
CSRF_TRUSTED_ORIGINS = ["http://localhost:8080"]

# Use the React development server when constructing verification links.
FRONTEND_BASE_URL = os.getenv(
    "FRONTEND_BASE_URL",
    "http://localhost:8080",
)


# Require secure session cookies when DEBUG is disabled.
SESSION_COOKIE_SECURE = not DEBUG

# Require secure CSRF cookies when DEBUG is disabled.
CSRF_COOKIE_SECURE = not DEBUG

# Prevent JavaScript from reading the session cookie.
SESSION_COOKIE_HTTPONLY = True

# Use same-site cookie behavior for local development.
SESSION_COOKIE_SAMESITE = "Lax"

# Use same-site behavior for the CSRF cookie.
CSRF_COOKIE_SAMESITE = "Lax"
# FRONTEND CONNECTION SETTINGS ENDs


# Application definition
# Define the applications enabled in this Django project.
INSTALLED_APPS = [
    "django.contrib.admin",  # Enable Django Admin.
    "django.contrib.auth",  # Enable Django authentication.
    "django.contrib.contenttypes",  # Enable Django content types.
    "django.contrib.sessions",  # Enable server-side sessions.
    "django.contrib.messages",  # Enable Django messages.
    "django.contrib.staticfiles",  # Enable static file handling.
    "rest_framework",  # Enable Django REST Framework.
    "corsheaders",  # Register CORS support.
    "drf_spectacular",  # Enable OpenAPI schema generation.
    "users",  # Register our custom user application.
    "api",  # Register the central API application.
]  # Finish the application configuration.

# MIDDLEWARE = [
#     'django.middleware.security.SecurityMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# ]


# Define the middleware that processes each Django request and response.
MIDDLEWARE = [
    # Add standard HTTP security protections.
    "django.middleware.security.SecurityMiddleware",
    # Manage browser sessions.
    "django.contrib.sessions.middleware.SessionMiddleware",
    # Handle permitted cross-origin requests.
    "corsheaders.middleware.CorsMiddleware",
    # Apply common HTTP request and response handling.
    "django.middleware.common.CommonMiddleware",
    # Protect unsafe requests against cross-site request forgery.
    "django.middleware.csrf.CsrfViewMiddleware",
    # Attach the authenticated user to each request.
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Enable Django's messaging framework.
    "django.contrib.messages.middleware.MessageMiddleware",
    # Protect against clickjacking.
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = 'BMS.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'BMS.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases

DATABASES = {
    "default": {
        # Tell Django to use PostgreSQL.
        "ENGINE": "django.db.backends.postgresql",
        # Read the database name from the environment.
        "NAME": os.getenv("DB_NAME"),
        # Read the database username from the environment.
        "USER": os.getenv("DB_USER"),
        # Read the database password from the environment.
        "PASSWORD": os.getenv("DB_PASSWORD"),
        # Read the database host from the environment.
        "HOST": os.getenv("DB_HOST"),
        # Read the database port from the environment.
        "PORT": os.getenv("DB_PORT"),
    }
}

# DATABASES = {
#     "default": dj_database_url.config(  # Build Django's database configuration from DATABASE_URL.
#         # Read the PostgreSQL connection URL from the .env file.
#         default=os.getenv("DATABASE_URL"),
#         # Keep database connections open for up to 600 seconds.
#         conn_max_age=600,
#     )
# }

# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = 'static/'


# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}

# Tell Django to use our custom User model for authentication, because we have extended the default user model to include additional fields like email and phone number. This setting ensures that all authentication-related operations will use our custom User model instead of the default one.
AUTH_USER_MODEL = "users.User"


# Configure Django REST Framework for the BMS API.
REST_FRAMEWORK = {
    # Use Django sessions for browser authentication initially.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    # Require explicit permission decisions for API endpoints.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # Use drf-spectacular to generate the OpenAPI schema.
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# Configure the metadata used to generate API documentation.
SPECTACULAR_SETTINGS = {
    # Set the API's displayed title.
    "TITLE": "Bank Management System API",
    # Describe the purpose of the API.
    "DESCRIPTION": "Versioned API for the Bank Management System.",
    # Set the initial API version.
    "VERSION": "1.0.0",
}
