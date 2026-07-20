# Orchestration (Airflow)

Airflow layer for the dbt platform. Deliberately small — two tasks per DAG — because the
interesting decisions are in the run modes and the testing, not in task count.

## The DAGs

One factory (`dags/dbt_platform.py`) produces two DAGs:

| DAG | Schedule | Build | Why it exists |
|---|---|---|---|
| `dbt_platform_daily` | 06:00 daily | `dbt build` (incremental) | Cheap steady-state refresh |
| `dbt_platform_weekly_full_refresh` | Sun 22:00 | `dbt build --full-refresh` | Bounds source-regeneration drift |

Both end with `scripts/qa_audit.py` as a **separate task** — verification gets its own
exit code and its own red square in the UI, instead of hiding inside the build step.

```
dbt_build  ─►  qa_audit
```

The weekly full refresh is not cargo-culted hygiene. `thelook_ecommerce` is a live public
dataset that Google periodically regenerates with reassigned keys, so an incremental fact
eventually carries orphans from a previous data generation. The relationships test catches
the drift when it happens ([receipts in the main README](../README.md#verification-receipts-not-claims));
the weekly rebuild bounds how long it can accumulate. Failure-mode details:
[`runbooks/qa-checklist.md`](../runbooks/qa-checklist.md).

## What CI verifies

`airflow-ci.yml` installs Airflow 3 and runs `pytest orchestration/tests` on every push/PR:

- every DAG file **imports cleanly** (DagBag has zero import errors — the classic
  "broken DAG in the scheduler" guard)
- the expected DAG ids exist, and **build precedes verification** in both
- run policy holds: `catchup=False`, every task has a retry policy
- only the weekly DAG passes `--full-refresh`

No warehouse credentials are needed — this job tests DAG structure, not data.

## Running it locally

Airflow requires Linux/macOS (or WSL/Docker on Windows):

```bash
pip install "apache-airflow==3.3.0" --constraint \
  "https://raw.githubusercontent.com/apache/airflow/constraints-3.3.0/constraints-3.12.txt"

# structure tests only (what CI runs)
pytest orchestration/tests

# full local scheduler + UI
export AIRFLOW__CORE__DAGS_FOLDER="$(pwd)/orchestration/dags"
airflow standalone
```

The DAGs locate the dbt project relative to their own path (the repo is the deployable
unit); override with `DBT_PROJECT_DIR`, `BQ_PROJECT`, `BQ_DATASET` for other layouts.
Warehouse auth is Application Default Credentials on the worker — no secrets in DAG code.
