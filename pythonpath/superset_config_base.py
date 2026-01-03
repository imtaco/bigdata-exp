"""
Superset base configuration

Shared configuration for all Superset services:
- Web server (superset)
- Celery worker (superset-worker)
- Celery beat scheduler (superset-beat)

Import this in service-specific configs:
    from superset_config_base import *

https://github.com/apache/superset/blob/465e2a9631994892cf399d13dd926c56cecd58ca/superset/config.py
"""

import os
from datetime import timedelta
from flask_caching.backends.rediscache import RedisCache


# ============================================================
# Database Configuration
# ============================================================

SQLALCHEMY_DATABASE_URI = os.environ.get("SUPERSET_DATABASE_URI")
CACHE_DEFAULT_TIMEOUT = 600

# ============================================================
# Session Configuration
# ============================================================

# TODO: https://github.com/apache/superset/blob/465e2a9631994892cf399d13dd926c56cecd58ca/superset/config.py#L1679

# ============================================================
# Celery Configuration
# ============================================================

class CeleryConfig(object):
    broker_url = "redis://redis:6379/0"
    result_backend = "redis://redis:6379/1"
    # Note: beat_schedule is added in worker config only

CELERY_CONFIG = CeleryConfig

SQLLAB_ASYNC_TIME_LIMIT_SEC = int(timedelta(minutes=30).total_seconds())


# ============================================================
# Redis Cache Configuration
# ============================================================

# Dashboard filter state cache (required)
FILTER_STATE_CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 86400,  # 1 day
    "CACHE_KEY_PREFIX": "superset_filter_cache_",
    "CACHE_REDIS_HOST": "redis",
    "CACHE_REDIS_PORT": 6379,
    "CACHE_REDIS_DB": 3,
}

# Data cache for chart/query results
DATA_CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 3600,  # 1 hour
    "CACHE_KEY_PREFIX": "superset_data_cache_",
    "CACHE_REDIS_HOST": "redis",
    "CACHE_REDIS_PORT": 6379,
    "CACHE_REDIS_DB": 2,
}

CACHE_CONFIG = DATA_CACHE_CONFIG

# ============================================================
# Feature Flags
# ============================================================

FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
    "ASYNC_QUERIES": True,
    "GLOBAL_ASYNC_QUERIES": True,
    "ALERT_REPORTS": True,
    "ALERTS_ATTACH_REPORTS": False,
}

# ============================================================
# Global Async Queries Configuration
# ============================================================

# JWT secret for async queries (read from env)
GLOBAL_ASYNC_QUERIES_JWT_SECRET = os.environ.get("GLOBAL_ASYNC_QUERIES_JWT_SECRET")

# Cache backend for async query results
GLOBAL_ASYNC_QUERIES_CACHE_BACKEND = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 86400,  # 1 day
    "CACHE_KEY_PREFIX": "async_queries_",
    "CACHE_REDIS_HOST": "redis",
    "CACHE_REDIS_PORT": 6379,
    "CACHE_REDIS_DB": 5,
}

# Transport mode for async queries
GLOBAL_ASYNC_QUERIES_TRANSPORT = "polling"  # Use polling mode (more stable)
GLOBAL_ASYNC_QUERIES_POLLING_DELAY = 1500  # Poll every 1.5 seconds (recommended by community)

# Results backend
# TODO: what if from ENV ?
# not related to Celery.result_backend
RESULTS_BACKEND = RedisCache(
    host=os.environ.get("REDIS_HOST"),
    port=int(os.environ.get("REDIS_PORT")),
    db=2,
    key_prefix="superset_results"
)

# ============================================================
# SQL Lab Settings
# ============================================================

SQLLAB_EXECUTE_ASYNC = True


# ============================================================
# Alert & Report Settings
# ============================================================

ENABLE_ALERTS = True


# ============================================================
# Superset Webserver URL Configuration
# ============================================================

SUPERSET_WEBSERVER_PROTOCOL = "http"
SUPERSET_WEBSERVER_ADDRESS = "localhost"
SUPERSET_WEBSERVER_PORT = 8088

# Enable proxy fix for Docker environments
# TODO: test
ENABLE_PROXY_FIX = True


# ============================================================
# WebDriver Configuration (Screenshot functionality)
# ============================================================
# Screenshot functionality is DISABLED (using CSV format instead)
# To enable screenshots:
# 1. Uncomment WebDriver settings below
# 2. Reinstall chromium and selenium in Dockerfile.superset
# 3. Rebuild Docker image

WEBDRIVER_TYPE = None
WEBDRIVER_BASEURL_USER_FRIENDLY = "http://localhost:8088/"

# WEBDRIVER_BASEURL = "http://superset:8088/"
# WEBDRIVER_TYPE = "chrome"
# WEBDRIVER_OPTION_ARGS = [
#     "--headless=new",
#     "--no-sandbox",
#     "--disable-dev-shm-usage",
#     "--disable-gpu",
#     "--disable-software-rasterizer",
#     "--disable-extensions",
#     "--disable-setuid-sandbox",
#     "--disable-web-security",
#     "--disable-features=VizDisplayCompositor",
#     "--disable-background-networking",
#     "--disable-default-apps",
#     "--disable-sync",
#     "--metrics-recording-only",
#     "--mute-audio",
#     "--no-first-run",
# ]
# WEBDRIVER_CONFIGURATION = {
#     "service_log_path": "/tmp/chromedriver.log",
# }
# WEBDRIVER_WINDOW = {
#     "dashboard": (1600, 1800),
#     "slice": (1000, 1200),
#     "pixel_density": 1,
# }
# SCREENSHOT_LOCATE_WAIT = 10
# SCREENSHOT_LOAD_WAIT = 30


# ============================================================
# Notification Configuration
# ============================================================

SLACK_API_TOKEN = "xxxx"

# Email notifications
EMAIL_NOTIFICATIONS = True
SMTP_HOST = "mailhog"
SMTP_PORT = 1025
SMTP_STARTTLS = False
SMTP_SSL = False
SMTP_USER = None
SMTP_PASSWORD = None
SMTP_MAIL_FROM = "admin@example.com"

# ============================================================
# Behavior Configuration
# ============================================================

APP_NAME = "CM Superset"
#APP_ICON = "https://aaa.bbb/ccc/ddd.png"

DASHBOARD_AUTO_REFRESH_INTERVALS = [
    [0, "Don't refresh"],
    # [180, "3 minute"],
    # [300, "5 minutes"],
    [600, "10 minutes"],
    [1800, "30 minutes"],
    [3600, "1 hour"],
]

SQL_MAX_ROW = 10000

# TODO: suervy
MUTATE_ALERT_QUERY = True

# TODO:
# too many "logs" in PG
# sql split for mutation