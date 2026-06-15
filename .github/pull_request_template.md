## What & why
<!-- One or two sentences: what does this PR change and why? -->

## Models touched
<!-- list models / marts added or modified -->

## Grain
<!-- State the grain of any new/changed model: "one row per ___" -->

## Checklist (see runbooks/model-review-checklist.md)
- [ ] Grain stated in model description and matches SQL
- [ ] `unique` + `not_null` on key; `relationships` on FKs
- [ ] Naming + layering conventions respected (no mart reads from source/staging)
- [ ] Appropriate materialization
- [ ] `dbt build` green in dev
- [ ] `python scripts/qa_audit.py` exits 0
- [ ] `dbt docs generate` clean
- [ ] No secrets / account identifiers committed

## Reviewer approval gate
<!-- Prod promotion requires reviewer sign-off. Do not self-merge to main. -->
