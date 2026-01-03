"""
Chart and Dashboard execution hooks

Hooks into chart/dashboard data loading to add:
- Force refresh support for GLOBAL_ASYNC_QUERIES
- Debug logging for async query execution
- Future: quota checking for chart queries
"""

import contextlib
from functools import wraps
from flask import request

from superset.charts.data.api import ChartDataRestApi
from superset.commands.chart.data.get_data_command import ChartDataCommand
from superset.commands.chart.exceptions import ChartDataCacheLoadError
from superset.commands.chart.data.create_async_job_command import CreateAsyncChartDataJobCommand
from superset.async_events.async_query_manager import AsyncQueryTokenException
from superset.utils.core import get_user_id


def install_chart_force_refresh_fix():
    """
    Fix Dashboard force refresh to use GLOBAL_ASYNC_QUERIES

    Superset 5.0.0 has a bug where force=true bypasses async queries.
    This patch ensures force refresh also uses async execution.
    """
    original_run_async = ChartDataRestApi._run_async

    @wraps(original_run_async)
    def patched_run_async(self, form_data, command):
        """
        Fixed _run_async: Skip cache check when force=True and use async execution
        """
        # When Dashboard force refresh, skip cache check and go async
        if not command._query_context.force:
            with contextlib.suppress(ChartDataCacheLoadError):
                result = command.run(force_cached=True)
                if result is not None:
                    return self._send_chart_response(result)

        # Use async execution
        async_command = CreateAsyncChartDataJobCommand()
        try:
            async_command.validate(request)
        except AsyncQueryTokenException:
            return self.response_401()

        result = async_command.run(form_data, get_user_id())
        return self.response(202, **result)

    ChartDataRestApi._run_async = patched_run_async
    print("✓ Fixed Dashboard force refresh to use GLOBAL_ASYNC_QUERIES")


def install_chart_debug_logging():
    """
    Install debug logging for chart data execution

    Logs important context about GLOBAL_ASYNC_QUERIES behavior
    """
    original_chart_run = CreateAsyncChartDataJobCommand.run
    # original_chart_validate = CreateAsyncChartDataJobCommand.validate

    # @wraps(original_chart_run)
    # def async_validate(self, **kwargs):
    #     """Log key information for debugging GLOBAL_ASYNC_QUERIES"""

    #     # Execute query
    #     result = original_chart_validate(self, **kwargs)

    #     print(results)
    #     return result

    @wraps(original_chart_run)
    def async_run(self, form_data, user_ids):
        """Log key information for debugging GLOBAL_ASYNC_QUERIES"""

        # Execute query
        result = original_chart_run(self, form_data, user_ids)
        return result

    # CreateAsyncChartDataJobCommand.validate = async_validate
    CreateAsyncChartDataJobCommand.run = async_run
    print("✓ Chart debug logging installed (CreateAsyncChartDataJobCommand.run)")


def install_chart_hooks():
    """Install all chart-related hooks"""
    install_chart_force_refresh_fix()
    # install_chart_debug_logging()
