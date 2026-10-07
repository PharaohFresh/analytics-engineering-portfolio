"""Airflow DAGs for the dbt analytics platform (build + independent verification).

Two DAGs from one factory, because the platform has two distinct run modes:

- ``dbt_platform_daily``            full-source keyed merge, runs every morning
- ``dbt_platform_weekly_full_refresh``  full-refresh rebuild, runs Sunday night

The weekly full refresh is not belt-and-braces: ``thelook_ecommerce`` is a live
public dataset that Google periodically regenerates (keys reassigned), so an
incremental fact eventually accumulates orphans against the rebuilt dimension
tables. The relationships test catches the drift; the scheduled full refresh
bounds how long the platform can carry it. See runbooks/qa-checklist.md.

Every run ends with scripts/qa_audit.py — verification is a separate task with
its own exit code, not a footnote inside the build.
"""

import os
import sys
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

# The repo is the deployable unit: dags/ ships inside the dbt project, so the
# project root is two levels up from this file. Overridable for deployments
# that mount the repo elsewhere.
PROJECT_DIR = os.environ.get(
    "DBT_PROJECT_DIR", str(Path(__file__).resolve().parents[2])
)
# Loading from a deployed repository works even when Airflow adds only dags/.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from orchestration.platform_config import audit_command, build_command, target_environment

TARGET_ENV = target_environment(os.environ, PROJECT_DIR)

DEFAULT_ARGS = {
    "owner": "analytics-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
}


def build_platform_dag(dag_id: str, schedule: str, full_refresh: bool) -> DAG:
    with DAG(
        dag_id=dag_id,
        description=(
            "dbt full-refresh rebuild + QA reconciliation"
            if full_refresh
            else "Incremental dbt build + QA reconciliation"
        ),
        schedule=schedule,
        start_date=pendulum.datetime(2026, 7, 1, tz="America/Chicago"),
        catchup=False,
        default_args=DEFAULT_ARGS,
        tags=["dbt", "bigquery", "governed-delivery"],
        doc_md=__doc__,
    ) as dag:
        dbt_build = BashOperator(
            task_id="dbt_build",
            bash_command=build_command(full_refresh),
            env=TARGET_ENV,
            append_env=True,
        )

        # Independent reconciliation (trust, but verify): re-counts grains and
        # orphans straight against BigQuery, outside dbt's own test framework.
        qa_audit = BashOperator(
            task_id="qa_audit",
            bash_command=audit_command(),
            env=TARGET_ENV,
            # Both tasks inherit worker authentication, without literal credentials.
            append_env=True,
        )

        dbt_build >> qa_audit

    return dag


daily = build_platform_dag(
    dag_id="dbt_platform_daily",
    schedule="0 6 * * *",
    full_refresh=False,
)

weekly_full_refresh = build_platform_dag(
    dag_id="dbt_platform_weekly_full_refresh",
    schedule="0 22 * * 0",
    full_refresh=True,
)
