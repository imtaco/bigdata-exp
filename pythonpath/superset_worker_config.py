"""
Superset Worker & Beat Configuration

This configuration is used by:
- superset-worker: Celery worker for async query execution
- superset-beat: Celery beat scheduler for periodic tasks (reports/alerts)

Imports shared configuration from superset_config_base.py and adds:
- Celery beat schedule (periodic tasks)
- Report execution hooks
- Worker-specific customizations
"""

from flask import Flask

# Import all shared configuration
from superset_config_base import *
from superset.config import CeleryConfig


# ============================================================
# Worker & Beat Specific Configuration
# ============================================================

# Override CeleryConfig to add beat schedule
class MyCeleryConfig(CeleryConfig):
    broker_url = "redis://redis:6379/0"
    result_backend = "redis://redis:6379/1"
    # imports = ('superset.tasks.scheduler',)
    # Beat schedule for periodic tasks (reports & alerts)
    # beat_schedule = {
    #     'reports.scheduler': {
    #         'task': 'reports.scheduler',
    #         'schedule': 60.0,  # Execute every 60 seconds
    #     },
    #     'reports.prune_log': {
    #         'task': 'reports.prune_log',
    #         'schedule': 3600.0,  # Execute every hour
    #     },
    # }

CELERY_CONFIG = MyCeleryConfig

# ============================================================
# Flask App Mutator (Worker & Beat)
# ============================================================

# def FLASK_APP_MUTATOR(app: Flask) -> None:
#     """
#     Superset calls this function during app initialization

#     We use it to install worker hooks:
#     - Report execution logging
#     - Celery task prerun checks

#     IMPORTANT: Import hooks here (not at module level) to avoid
#     importing Superset modules before the app context is ready.
#     """
#     print("=== Worker: Initializing hooks ===")

#     # Import hooks only when app is ready
#     from hooks.report_hooks import install_report_hooks

#     # Install report execution hooks
#     install_report_hooks()

#     print("=== Worker: All hooks installed successfully ===")


# import hooks.report_hooks

def SQL_QUERY_MUTATOR(  # pylint: disable=invalid-name,unused-argument  # noqa: N802
    sql, **kwargs
) -> str:
    from hooks.sql_logging import sql_query_mutator
    sql_query_mutator(sql, **kwargs)
    return sql
