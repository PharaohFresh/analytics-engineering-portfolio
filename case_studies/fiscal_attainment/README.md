# Fiscal sales and plan: from item grain to a stakeholder decision

This module turns a validated finance contract into an interactive review. It answers three questions: How much order value remains after returns? Which planned buckets are below target? What data or planning gaps could make an aggregate percentage misleading?

The original offline fixture has nine item records, with eight inside February-April 2026. A cancelled item contributes no value; a returned item contributes to gross and returned value; an item in May stays outside the cohort. An unmapped department remains visible. The resulting nine month/department buckets contain **97,000 cents gross, 8,000 returned and 89,000 retained**, with **49,000 cents indicative retained margin**. March/Women stays visible at zero value against an 18,000-cent plan. April/Women has a declared zero plan; April/Unmapped has no plan. Those states are deliberately different.

## Review the working view

The Pages workflow publishes the [warehouse-backed dashboard](https://pharaohfresh.github.io/analytics-engineering-portfolio/dashboard/) alongside the [dbt catalog](https://pharaohfresh.github.io/analytics-engineering-portfolio/). The source label on each view distinguishes public warehouse data from the original offline fixture. Targets are invented in both cases. The public plan scales the small [fixture targets](fixtures/targets.csv) by 1,000 to fit the public dataset's demonstration scale while retaining the same period/department coverage and zero target. Neither plan is a real business budget or evidence of actual target performance. The dashboard includes a three-step, roughly 60-second walkthrough; no login or BI license is required.

For an offline copy:

```text
python -m case_studies.fiscal_attainment --output artifacts/fiscal-demo
python -m http.server 8765 --directory artifacts/fiscal-demo --bind 127.0.0.1
```

Open `http://127.0.0.1:8765`. The output directory must be new. Stop the server with Ctrl+C. [The generated fixture report](example-report.json) is also inspectable without running anything.

## Contracts and decisions

| Contract | Implemented behavior | Stakeholder implication |
|---|---|---|
| Item grain | Reject duplicate item keys; integer cents rounded per source item | A join cannot silently multiply financial value |
| Completed date cohort | Item-created dates February 1 inclusive, May 1 exclusive; current item state | Later return updates can restate an earlier item month |
| Fiscal calendar | February start; named by ending year; calendar-month periods | FY2027/FM01 means February 2026, not an employer's 4-4-5 calendar |
| Full month coverage | Three-month spine crossed with actual/planned departments | An empty period cannot disappear from attainment |
| Missing versus zero target | Missing plan remains null; a zero plan is a declared value | Unknown coverage is different from unplanned activity against a zero goal |
| Attainment | Sum of plan-covered retained value / sum of targets | Recalculate after filtering; never average department percentages |
| Unmapped department | Included under Unmapped with explicit plan coverage | Keep valid value while someone resolves mapping/ownership |
| Margin | Retained value less retained units' current product cost | Indicative margin is not historical COGS or accounting profit |

“Retained order value” includes unfulfilled orders and subtracts the full sale value of currently returned items. It is an operational cohort measure, **not settled cash, verified refunds or GAAP revenue**. The illustrative targets demonstrate mechanics and cannot substantiate business performance. No causal diagnosis or forecast is inferred.

The public model is [mart_fiscal_attainment](../../models/marts/finance/mart_fiscal_attainment.sql), at month/department grain. It reads the existing item fact and [invented target seed](../../seeds/demo_fiscal_targets.csv). The [SQL contract](../../tests/fiscal_contracts.sql) checks mart/plan uniqueness, nonnegative targets and the gross-minus-returned identity.

Before publishing the warehouse-backed view, the [Python builder](__main__.py) independently recomputes every bucket from the item fact and compares keys and all metric/target values against the dbt mart. Same-count corruption, missing rows and duplicated rows block publication. This verifies the mart against its parent fact; the existing eleven independent source-to-fact QA checks remain the separate upstream assurance.

## What the walkthrough demonstrates

1. Read the origin and metric definitions before interpreting a high aggregate attainment number.
2. Filter March/Women: the fixture keeps its empty month and target visible. Investigate volume, returns and the plan assumptions rather than assigning a cause from a chart.
3. Filter April: distinguish zero-target activity from missing plan coverage. Preserve unplanned value outside the attainment numerator and make the ownership question explicit.

The offline fixture and public warehouse have different actual values. The walkthrough steps guide inspection; they are not claims that the public source reproduces the fixture's March gap. Run `python -m pytest offline_tests -q` for period boundaries, return restatement, duplicate keys, invalid states, missing/zero plans and publication-blocking mart corruption.
