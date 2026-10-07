from __future__ import annotations

from collections.abc import Mapping


def target_environment(environment: Mapping[str, str], project_dir: str) -> dict[str, str]:
    target = environment.get("DBT_TARGET", "dev")
    datasets = {"dev": "dbt_dev", "prod": "analytics"}
    if target not in datasets:
        raise ValueError("DBT_TARGET must be dev or prod for these deployment DAGs.")
    project = environment.get("BQ_PROJECT", "career-analytics-portfolio")
    dataset = environment.get("BQ_DATASET", datasets[target])
    if not project or not dataset or not project_dir:
        raise ValueError("Project, dataset and project directory must be explicit nonempty values.")
    return {"DBT_TARGET": target, "BQ_PROJECT": project, "BQ_DATASET": dataset, "DBT_PROJECT_DIR": project_dir}


def build_command(full_refresh: bool) -> str:
    return 'cd "$DBT_PROJECT_DIR" && dbt build --target "$DBT_TARGET"' + (" --full-refresh" if full_refresh else "")


def audit_command() -> str:
    return 'cd "$DBT_PROJECT_DIR" && python scripts/qa_audit.py'
