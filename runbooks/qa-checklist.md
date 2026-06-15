# Runbook: QA Checklist (pre-merge)

Run before requesting review.

1. `dbt build` — all models + tests green in dev.
2. `dbt snapshot` — snapshot runs without error.
3. `python scripts/qa_audit.py` — exit code 0 (row-count + integrity reconciliation).
4. `dbt docs generate` — no compilation warnings; lineage looks right.
5. Spot-check one mart's numbers against a hand-written query (sanity, not just green tests).
6. Confirm `git status` shows no `profiles.yml`, `.env`, or `target/` staged.
