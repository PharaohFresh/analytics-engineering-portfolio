# Runbook: QA before requesting merge review

1. Run `python -m pytest offline_tests -q` and reproduce both case studies.
2. Set `DBT_TARGET=dev`, `BQ_PROJECT` and `BQ_DATASET` to the same profile output.
3. Run `dbt build --target dev`; all models, data tests and snapshot must pass.
4. Run `python scripts/qa_audit.py`; all eleven read-only contracts must pass.
5. Generate dbt docs and inspect lineage/model descriptions.
6. Spot-check the finance marts' grain and reported totals against source.
7. Check staged files for populated profiles, credentials, environments, logs and generated targets.
8. Attach actual commands/results and any checks not run to the PR. Obtain human review before production promotion.

## Mutable items: daily keyed merge

The fact selects the complete current enrichment rather than filtering on item creation time. Verify an older returned item, a new tied timestamp and a late-arriving older timestamp. Current product cost/category changes also refresh prior items. This reference policy scans all source rows.

## Source deletion or generation replacement

An incremental merge does not delete disappeared keys. Independent source/fact key coverage and row counts can fail; relationships also fail when retained items have lost parents. A stable orphan count is a symptom, not proof of a particular upstream cause.

Inspect source key sets and provenance before attributing the failure to regeneration. For the sample dataset, realign the development fact with a reviewed `dbt build --target dev --full-refresh`. Re-run all QA and finance tests. Do not delete individual rows manually or rebuild the append-only product snapshot destructively.

## Counts pass, values do not

The independent keyed check catches changed sale prices, parent mappings, return state and current product enrichment, including equal-and-opposite price errors. Diagnose the failing item IDs against the exact built target; do not accept an unchanged grand total as proof of correctness.
