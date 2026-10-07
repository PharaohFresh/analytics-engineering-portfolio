"""DagBag tests: every DAG in orchestration/dags must import cleanly and keep
its contract (ids, dependencies, retry policy, no accidental catchup).

Run:  pytest orchestration/tests
CI runs this on every push/PR (see .github/workflows/airflow-ci.yml).
"""

from pathlib import Path
from datetime import timedelta

import pytest
from airflow.models.dagbag import DagBag

DAGS_DIR = Path(__file__).resolve().parents[1] / "dags"

EXPECTED_DAGS = {
    "dbt_platform_daily",
    "dbt_platform_weekly_full_refresh",
}


@pytest.fixture(scope="session")
def dagbag() -> DagBag:
    # Airflow 3 DagBag no longer takes include_examples; it only parses dag_folder.
    return DagBag(dag_folder=str(DAGS_DIR))


def test_no_import_errors(dagbag):
    assert dagbag.import_errors == {}, (
        f"DAG import failures: {dagbag.import_errors}"
    )


def test_expected_dags_present(dagbag):
    assert set(dagbag.dag_ids) == EXPECTED_DAGS


# dagbag.dags reads the parsed DAG objects directly; get_dag() would hit the
# (nonexistent in CI) metadata DB for a staleness check.
@pytest.mark.parametrize("dag_id", sorted(EXPECTED_DAGS))
def test_build_precedes_verification(dagbag, dag_id):
    dag = dagbag.dags[dag_id]
    assert set(dag.task_ids) == {"dbt_build", "qa_audit"}
    assert dag.get_task("qa_audit").upstream_task_ids == {"dbt_build"}


@pytest.mark.parametrize("dag_id", sorted(EXPECTED_DAGS))
def test_run_policy(dagbag, dag_id):
    dag = dagbag.dags[dag_id]
    assert dag.catchup is False, "backfilling a live public source is meaningless"
    for task in dag.tasks:
        assert task.retries >= 1, f"{task.task_id} has no retry policy"
        assert task.retry_exponential_backoff is True
        assert task.retry_delay == timedelta(minutes=5)
        assert task.max_retry_delay == timedelta(minutes=30)


def test_only_weekly_dag_full_refreshes(dagbag):
    def build_command(dag_id):
        return dagbag.dags[dag_id].get_task("dbt_build").bash_command

    assert "--full-refresh" not in build_command("dbt_platform_daily")
    assert "--full-refresh" in build_command("dbt_platform_weekly_full_refresh")


@pytest.mark.parametrize("dag_id", sorted(EXPECTED_DAGS))
def test_build_and_audit_have_identical_explicit_target(dagbag, dag_id):
    dag = dagbag.dags[dag_id]
    build = dag.get_task("dbt_build")
    audit = dag.get_task("qa_audit")
    assert build.env == audit.env
    assert build.env["DBT_TARGET"] in {"dev", "prod"}
    assert build.env["BQ_DATASET"]
    assert '--target "$DBT_TARGET"' in build.bash_command
    assert build.append_env is True and audit.append_env is True
