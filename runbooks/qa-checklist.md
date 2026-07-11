# Runbook: QA Checklist (pre-merge)

Run before requesting review.

1. `dbt build` — all models + tests green in dev.
2. `dbt snapshot` — snapshot runs without error.
3. `python scripts/qa_audit.py` — exit code 0 (row-count + integrity reconciliation).
4. `dbt docs generate` — no compilation warnings; lineage looks right.
5. Spot-check one mart's numbers against a hand-written query (sanity, not just green tests).
6. Confirm `git status` shows no `profiles.yml`, `.env`, or `target/` staged.

## Known failure mode: source regeneration drift

`thelook_ecommerce` is a live public dataset that Google periodically regenerates.
An incremental model retains rows from the previous data generation, so the
`relationships` test on `fct_order_items.order_key` can fail with orphaned keys
after a regeneration even though no code changed.

- **Diagnose:** the failing rows' `item_created_at` predate the current source's
  earliest `orders.created_at` generation, and the orphan count is stable across runs.
- **Resolve:** `dbt build --full-refresh` to realign incremental state with the
  current source generation. Never delete rows by hand.
