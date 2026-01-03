"""
SQL Query Logging & Monitoring

This module provides hooks for logging SQL queries before execution,
including user information and database context.

Shared between web server and Celery workers.
"""

# import threading
from typing import Any

# Thread-local storage for sharing data between Celery hooks and SQL_QUERY_MUTATOR
# _thread_local = threading.local()

# def cleanup_thread_local():
#     """Clean up all thread-local variables"""
#     for attr in ['in_chart_cache_task', 'chart_user_id', 'chart_id', 'datasource']:
#         if hasattr(_thread_local, attr):
#             try:
#                 delattr(_thread_local, attr)
#             except Exception:
#                 pass

def sql_query_mutator(sql: str, **kwargs: Any) -> str:
    """
    Args:
        sql: The SQL query string
        **kwargs: Additional context (database, security_manager, etc.)

    Returns:
        str: The SQL query string (potentially modified)
    """
    try:
        # if not getattr(_thread_local, 'in_chart_cache_task', False):
            # return sql
        # user_id = getattr(_thread_local, 'chart_user_id', None)
        user_email = None
        user_name = None
        flask_username = None

        try:
            from flask import g
            if hasattr(g, 'user') and g.user:
                user_email = getattr(g.user, 'email', None)
                user_name = getattr(g.user, 'username', None)
                flask_username = user_name
                print(f"[SQL Execution] Got user from g.user: {user_name}")
        except Exception as e:
            print(f"[SQL Execution] Could not get user from g.user: {e}")

        if not flask_username:
            try:
                from superset.utils.core import get_username
                flask_username = get_username()
                if flask_username:
                    print(f"[SQL Execution] Got username from get_username(): {flask_username}")
            except Exception as e:
                print(f"[SQL Execution] Could not get username: {e}")

        database = kwargs.get('database')
        db_backend = database.backend if database else 'Unknown'

        print(f"[SQL Execution] ========================================")
        print(f"[SQL Execution] BEFORE SQL EXECUTION")
        print(f"[SQL Execution] ========================================")
        # print(f"[SQL Execution] User ID: {user_id}")
        print(f"[SQL Execution] User Email: {user_email}")
        print(f"[SQL Execution] Username: {user_name or flask_username}")
        print(f"[SQL Execution] DB Engine: {db_backend}")
        print(f"[SQL Execution] ----------------------------------------")
        print(f"[SQL Execution] SQL Query:")
        print(f"{sql}")
        print(f"[SQL Execution] ========================================")

        sql = f"--run: {user_email}\n{sql}"

    except Exception as e:
        print(f"[SQL Execution] Error in sql_query_mutator: {e}")
        import traceback
        traceback.print_exc()
    return sql


# def set_chart_cache_context(user_id: Any, chart_id: Any, datasource: Any):
#     """
#     Set thread-local context for chart cache queries

#     Args:
#         user_id: User ID from job_metadata
#         chart_id: Chart/slice ID from form_data
#         datasource: Datasource identifier from form_data
#     """
#     try:
#         _thread_local.in_chart_cache_task = True
#         _thread_local.chart_user_id = user_id
#         _thread_local.chart_id = chart_id
#         _thread_local.datasource = datasource
#     except Exception as e:
#         print(f"[SQL Logging] Error setting context: {e}")
#         cleanup_thread_local()
