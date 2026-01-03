"""
SQL Lab execution hooks

Hooks into SQL Lab query execution to add:
- Per-user quota checking before query execution
- Query cost tracking and recording
"""

from functools import wraps
from flask import g
from superset.commands.sql_lab.execute import ExecuteSqlCommand

from hooks.quota import (
    UserQuotaExceeded,
    calculate_query_cost,
    get_user_quota_usage,
    get_user_quota_limit,
    record_quota_usage,
)


def install_sqllab_quota_hook():
    """
    Install quota checking hook for SQL Lab queries

    This hooks into ExecuteSqlCommand.run() to check user quota
    before submitting queries to Celery workers.
    """
    original_run = ExecuteSqlCommand.run

    @wraps(original_run)
    def run_with_quota_check(self):
        """Check quota before submitting Celery task"""

        # Get user email
        user_email = None
        if hasattr(g, 'user') and g.user:
            user_email = g.user.email

            # Get SQL from execution_context (query doesn't exist yet)
            sql = self._execution_context.sql

            # 1. Calculate query cost
            cost = calculate_query_cost(user_email, sql)

            # 2. Check quota
            current_usage = get_user_quota_usage(user_email)
            quota_limit = get_user_quota_limit(user_email)

            print(f"[Web Quota] User: {user_email}, SQL: {sql[:100]}...")
            print(f"[Web Quota] Usage: {current_usage}/{quota_limit}, Cost: {cost}")

            if current_usage + cost > quota_limit:
                raise UserQuotaExceeded(
                    f"User {user_email} exceeded daily quota. "
                    f"Used: {current_usage}, Limit: {quota_limit}, Query Cost: {cost}"
                )

            # 3. Execute original run (creates query and submits to Celery)
            result = original_run(self)

            # 4. Record quota usage after query is created
            if hasattr(self._execution_context, 'query') and self._execution_context.query:
                query_id = self._execution_context.query.id
                record_quota_usage(query_id, user_email, sql, cost)
                print(f"[Web Quota] Recorded quota for query {query_id}")

            return result
        else:
            print("[Web Quota] No user found, skip quota check")
            return original_run(self)

    # Replace original method
    ExecuteSqlCommand.run = run_with_quota_check
    print("✓ SQL Lab quota hook installed (ExecuteSqlCommand.run)")
