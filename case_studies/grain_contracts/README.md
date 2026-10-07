# Case study: preserve financial grain through customization joins

A physical retail unit can have several customization records: engraving, color, placement or packaging. Joining those child records directly to the sale repeats its price. An inner join to an incomplete product catalog can create the opposite error by silently dropping a valid sale.

This original SQLite example reproduces both problems and fixes the reporting join. All orders, products, designs and amounts are invented.

## Two-minute review

1. Read the [source fixture](fixtures/seed.sql): three orders, five physical units and seven customization records.
2. Inspect [the corrected query](fixtures/grain_safe.sql): aggregate customization records to item grain, then left join that result and product metadata.
3. Compare the [reproducible report](example-report.json).

| Calculation | Physical/report rows | Revenue |
|---|---:|---:|
| Source item contract | 5 | 50,000 cents |
| Direct customization join | 8 | 85,000 cents |
| Inner product join | 4 | 38,000 cents |
| Corrected item-grain query | 5 | 50,000 cents |

The missing product record remains visible as `Unmapped`; it still contributes its 12,000 cents. The three orders and seven design records remain separate metrics rather than being presented as eight sales.

## Run it

From the repository root, Python 3.12 or newer is sufficient; the demo uses only the standard library.

```bash
python -m case_studies.grain_contracts --output artifacts/grain
```

The command writes `artifacts/grain/report.json`. To run the regression suite:

```bash
python -m pip install -r requirements-offline.txt
python -m pytest offline_tests/test_case_studies.py -q
```

Tests reject duplicate/null item keys, duplicate catalog keys, missing parents and fractional amounts. The evaluator also compares the corrected result's item ID, parent order and money against the source row by row; unchanged totals alone would not prove a safe join.

## Design decisions

- **One item means one physical unit in this fixture.** Quantity lines, split fulfillment and bundle allocation require different contracts.
- **Customization is metadata here.** It has no separate price. This does not implement any company's manufacturing or pricing rules.
- **Preserve a valid sale with missing descriptive metadata.** Surface the unmapped category for repair rather than erasing revenue.
- **Use integer cents.** The demo performs exact comparisons and does not round a join error away.
- **Validate the many-to-one side.** A duplicate product key would still multiply rows after preaggregating customization, so it fails before reporting.

This is a focused local reference implementation. It demonstrates business grain and reconciliation, without claiming production deployment, employer results or unseen-data correctness.

[Return to the platform](../../README.md)
