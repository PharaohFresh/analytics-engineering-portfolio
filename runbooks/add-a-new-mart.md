# Runbook: Add a New Mart

Declarative steps to add a business mart without breaking the platform's guarantees.

1. **Define the grain first.** Write it in one sentence before any SQL ("one row per ___"). If you can't, stop.
2. **Build upstream, not sideways.** A mart reads from `marts/core` (dims/facts) or `intermediate/`, never directly from `staging` or `source`.
3. **Create the model** under the correct domain folder (`marts/finance/`, etc.).
4. **Add it to `_marts.yml`:** description, the grain restated, and at minimum a `unique` + `not_null` test on its key.
5. **Build in dev:** `dbt build --select +my_new_mart` (runs the model and its upstream + tests).
6. **Reconcile:** run `python scripts/qa_audit.py` (add a check if the mart introduces a new grain to defend).
7. **Document:** confirm `dbt docs generate` renders the description and lineage.
8. **PR:** open against `main`, fill the PR template, request review. Do not self-merge to prod.
