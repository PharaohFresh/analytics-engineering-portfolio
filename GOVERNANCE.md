# Governance and implemented boundaries

This public reference keeps development and production concepts explicit. The included offline demos use invented records; BigQuery CI builds the personal `dbt_ci` dataset. No employer systems or production deployment are connected.

## Environments and promotion

The profile offers separate `dev` (`dbt_dev`) and `prod` (`analytics`) outputs. Development runs use `dev`; no production build runs from a laptop. Airflow resolves an explicit target and gives build/QA the same project/dataset.

Before production promotion:

1. Build and verify the exact change in development.
2. Open a PR with the model-review checklist and actual test results.
3. Obtain human reviewer approval. No self-merge to production.
4. Promote through the authorized protected-main pipeline and verify the target independently.

These are deployment requirements. The current Actions pipeline builds `dbt_ci` and can publish a catalog after a green `main` build; it does not deploy the `prod` output. Profile names and this file do not establish effective permissions or branch-protection settings.

## No-deletion policy

Deprecate model definitions before removing them; retain a deprecation alias for one cycle when renaming. Product snapshots are append-only history and are not destructively rebuilt. A reviewed full refresh of the item fact is a separate data-state realignment after source disappearance/regeneration, not permission to erase snapshot history or drop unrelated models.

## Data integrity

Core/source keys have generic dbt tests. Finance marts have explicit composite-grain and total-reconciliation tests. Independent Python QA checks counts, null/duplicate keys, bidirectional source coverage, relationships and item values/parent mappings by key. Offline tests reproduce failure modes; credentialed warehouse checks verify the actual engine.

## Secrets and source boundaries

Local authentication uses worker Application Default Credentials. CI's service-account key comes from a repository secret into the runner's temporary directory. Populated profiles, environment files, credentials, datasets and generated build/log artifacts stay outside commits. Public demonstrations use original synthetic fixtures and contain no employer source or private records.

## Recovery

Reverting code does not itself restore external state. Rebuild the approved development target, run independent readback and follow provider-specific production recovery where applicable. Fact full refresh does not authorize destructive snapshot recovery.
