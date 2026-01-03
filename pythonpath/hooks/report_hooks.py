"""
Report and Alert execution hooks (Worker-side)

Hooks into report/alert execution to add:
- Debug logging for report execution
- Owner and content information tracking
- Future: Per-user quota checking for reports
"""

from functools import wraps
from celery.signals import task_prerun, task_postrun

# from superset.commands.report.execute import AsyncExecuteReportScheduleCommand
# from superset.commands.chart.data.get_data_command import ChartDataCommand

# Import shared SQL logging utilities
from hooks.sql_logging import set_chart_cache_context, cleanup_thread_local

# def install_report_execution_logging():
#     """
#     Install debug logging for report execution

#     Hooks into AsyncExecuteReportScheduleCommand to log report details
#     when they execute in Celery workers.
#     """
#     original_run = AsyncExecuteReportScheduleCommand.run

#     @wraps(original_run)
#     def run_with_debug(self):
#         """Log report information during execution"""
#         print(f"[Report Execute] ========== Report execution starting ==========")

#         # Execute original run (which calls validate internally)
#         result = original_run(self)

#         # Now self._model should be set, print information
#         if self._model:
#             print(f"[Report Execute] Report ID: {self._model.id}, Name: {self._model.name}")
#             print(f"  Type: {self._model.type}")

#             # Print owners
#             if self._model.owners:
#                 owners = ', '.join([o.email for o in self._model.owners if o.email])
#                 print(f"  Owners: {owners}")

#             # Print SQL or Chart information
#             if self._model.sql:
#                 print(f"  SQL: {self._model.sql}")
#             elif self._model.chart:
#                 print(f"  Chart: {self._model.chart.slice_name} (ID: {self._model.chart_id})")
#                 if self._model.dashboard:
#                     print(f"  Dashboard: {self._model.dashboard.dashboard_title} (ID: {self._model.dashboard_id})")

#             print(f"[Report Execute] ========== Report {self._model.id} finished ==========")

#         return result

#     AsyncExecuteReportScheduleCommand.run = run_with_debug
#     print("✓ Worker: Hooked AsyncExecuteReportScheduleCommand.run successfully")


@task_prerun.connect
def check_quota_before_celery_task(task_id=None, task=None, args=None, kwargs=None, **extra):
    """
    Pre-execution check for Celery tasks

    This is a secondary validation to prevent bypassing web server checks
    """
    try:
        if not task:
            return

        print(f"[Worker Task] Running task: {task.name}")

        # Handle reports.execute
        if task.name == 'reports.execute':
            print("[Report Execute Debug] ========== reports.execute starting ==========")
            # Future: Add quota checking here if needed
            # Currently just logging for debugging
        elif task.name == 'load_chart_data_into_cache':
            pass
            # load_chart_data_into_cache 的簽名: (job_metadata, form_data)
            # if args and len(args) >= 2:
            #     job_metadata = args[0]
            #     form_data = args[1]
            #     print(f"[Chart Cache] Got params from args")
            # else:
            #     job_metadata = kwargs.get('job_metadata', {})
            #     form_data = kwargs.get('form_data', {})
            #     print(f"[Chart Cache] Got params from kwargs")

            # user_id = job_metadata.get('user_id') if job_metadata else None
            # chart_id = form_data.get('slice_id') if form_data else None
            # datasource = form_data.get('datasource') if form_data else None

            # print(f"[Chart Cache] ========== Chart cache task starting ==========")
            # print(f"[Chart Cache] User ID: {user_id}")
            # print(f"[Chart Cache] Chart ID: {chart_id}")
            # print(f"[Chart Cache] Datasource: {datasource}")

            # set_chart_cache_context(user_id, chart_id, datasource)


    except Exception as e:
        # Log errors but don't block execution
        print(f"[Worker Task] Error in prerun hook: {e}")
        import traceback
        traceback.print_exc()
        cleanup_thread_local()

@task_postrun.connect
def cleanup_after_task(task_id=None, task=None, **kwargs):
    """
    Clean up thread-local variables after task execution
    """
    try:
        if task and task.name == 'load_chart_data_into_cache':
            print(f"[Chart Cache] ========== Chart cache task completed ==========")
            cleanup_thread_local()
    except Exception as e:
        print(f"[Worker Task] Error in postrun hook: {e}")
        import traceback
        traceback.print_exc()

# def install_report_hooks():
#     """Install all report-related hooks (Worker-side only)"""
#     # install_report_execution_logging()
#     # install_celery_task_prerun_hook()
#     # install_chart_data_logging()
#     print("=== Worker: All report hooks installed ===")
