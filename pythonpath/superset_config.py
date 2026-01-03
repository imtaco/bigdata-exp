"""
Superset Web Server Configuration

This configuration is used by the Superset web server container.

Imports shared configuration from superset_config_base.py and adds:
- SQL Lab quota hooks
- Chart/Dashboard hooks
- Web-specific customizations
"""

from flask import Flask

# Import all shared configuration
from superset_config_base import *


# ============================================================
# Web Server Specific Configuration
# ============================================================

# Additional web-specific settings can go here
# (Currently all settings are shared in base config)


# ============================================================
# Flask App Mutator (Web Server)
# ============================================================

def FLASK_APP_MUTATOR(app: Flask) -> None:
    """
    Superset calls this function during app initialization

    We use it to install web server hooks:
    - SQL Lab quota checking
    - Chart/Dashboard force refresh fix
    - Chart debug logging

    IMPORTANT: Import hooks here (not at module level) to avoid
    importing Superset modules before the app context is ready.
    """
    print("=== Web Server: Initializing hooks ===")

    # Import hooks only when app is ready
    # from hooks.sqllab_hooks import install_sqllab_quota_hook
    from hooks.chart_hooks import install_chart_hooks

    # Install SQL Lab quota hook
    # install_sqllab_quota_hook()

    # Install Chart/Dashboard hooks
    install_chart_hooks()
    print("=== Web Server: All hooks installed successfully ===")

def SQL_QUERY_MUTATOR(  # pylint: disable=invalid-name,unused-argument  # noqa: N802
    sql, **kwargs
) -> str:
    from hooks.sql_logging import sql_query_mutator
    sql_query_mutator(sql, **kwargs)
    return sql
