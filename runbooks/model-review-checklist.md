# Runbook: Model Review Checklist

What a reviewer confirms before approving a PR to `main` (prod).

- [ ] **Grain** is stated in the model's `description` and matches the SQL (no accidental fan-out).
- [ ] **Key tests** present: `unique` + `not_null` on the primary/surrogate key.
- [ ] **Referential tests** (`relationships`) on foreign keys where a parent exists.
- [ ] **Naming** follows convention (`stg_`, `int_`, `dim_`, `fct_`, `mart_`); columns renamed in staging, not marts.
- [ ] **Materialization** is appropriate (views for staging, tables for marts, incremental for high-volume facts).
- [ ] **No source/`staging` references** from a mart — layering respected.
- [ ] **`dbt build` passes** in dev with zero failures; `qa_audit.py` reconciles.
- [ ] **No secrets** added to the repo; no hard-coded account identifiers.
- [ ] **Docs** render correctly (`dbt docs generate`).
