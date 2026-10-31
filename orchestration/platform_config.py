from __future__ import annotations

from collections.abc import Mapping

# Each profile output reads its own variable, so a dataset exported for dev cannot redirect prod.
DATASET_VARIABLES = {"dev": ("BQ_DEV_DATASET", "dbt_dev"), "prod": ("BQ_PROD_DATASET", "analytics")}


def target_environment(environment: Mapping[str, str], project_dir: str) -> dict[str, str]:
    target = environment.get("DBT_TARGET", "dev")
    if target not in DATASET_VARIABLES:
        raise ValueError("DBT_TARGET must be dev or prod for these deployment DAGs.")
    dataset_variable, default_dataset = DATASET_VARIABLES[target]
    project = environment.get("BQ_PROJECT", "career-analytics-portfolio")
    dataset = environment.get(dataset_variable, default_dataset)
    if not project or not dataset or not project_dir:
        raise ValueError("Project, dataset and project directory must be explicit nonempty values.")
    # BQ_DATASET is derived for the QA task and overrides any inherited worker value.
    return {
        "DBT_TARGET": target,
        "BQ_PROJECT": project,
        dataset_variable: dataset,
        "BQ_DATASET": dataset,
        "DBT_PROJECT_DIR": project_dir,
    }


def build_command(full_refresh: bool) -> str:
    return 'cd "$DBT_PROJECT_DIR" && dbt build --target "$DBT_TARGET"' + (" --full-refresh" if full_refresh else "")


def audit_command() -> str:
    return 'cd "$DBT_PROJECT_DIR" && python scripts/qa_audit.py'
