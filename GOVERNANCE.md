# Governance

This repo models the same governance discipline I run on production platforms — the part most
portfolios skip. The point isn't ceremony; it's that data people can *trust* what ships.

## Environments
- **dev** and **prod** are separate Snowflake databases (`ANALYTICS_DEV` / `ANALYTICS_PROD`), selected by dbt target.
- All development happens against `dev`. Nothing runs against `prod` from a laptop.

## Promotion (dev → prod)
1. Build and test in `dev`: `dbt build` must pass (models + tests) with zero failures.
2. Open a PR. The PR template (`.github/pull_request_template.md`) encodes the model-review checklist.
3. **Human approval gate:** a reviewer signs off before merge. No self-merge to `prod`.
4. `prod` builds run only from the protected `main` branch via the approved pipeline.

## No-deletion policy
- Models are deprecated, not dropped, on first pass. Renames go through a deprecation alias for one cycle.
- Snapshots are append-only history and are never rebuilt destructively.

## Data integrity
- Every source has defined tests; every mart asserts its grain (unique key + not_null).
- `scripts/qa_audit.py` reconciles row counts staging → marts as an independent check (trust, but verify).

## Secrets
- Credentials live only in `~/.dbt/profiles.yml` (gitignored). `profiles.yml.example` is the template.
- No keys, passwords, or account identifiers are ever committed.

## Rollback
- Because promotion is PR-based and `prod` is rebuildable from version-controlled code, rollback = revert the commit and rerun the pipeline.
