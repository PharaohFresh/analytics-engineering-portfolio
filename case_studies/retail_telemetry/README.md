# Case study: complete-session checkout telemetry

Checkout logs have several grains: event delivery, payment attempt, authorization and session. Confusing those grains can turn a replay into another payment or a recovered decline into a double-charge alarm. Filtering only the session's starting calendar partition can also miss a successful payment after midnight.

This original offline model uses five invented sessions and fifteen events. It joins by explicit session identity and declared time interval rather than guessing from nearby timestamps. No retailer logs, payment credentials, device IDs or live services are included.

## Two-minute review

Inspect the [fixture](fixtures/events.json), [model](./__init__.py) and [generated report](example-report.json).

| Session | Observed behavior | Model result |
|---|---|---|
| Normal checkout | One approved authorization; a slow routine API call | No authorization-review flag |
| Recovered retry | Decline followed by one approval | Retry recovery; no duplicate-authorization flag |
| Review candidate | Two distinct approved authorization references | Candidate for provider/settlement review |
| Printer failure | Approval followed by a printer failure | Peripheral incident, separate from payment status |
| Cross-midnight checkout | Decline before midnight, approval after midnight | Complete session includes both partitions |

The midnight session has one successful authorization. A start-date-only filter finds zero. The report retains both values to make the omission observable.

## Run it

From the repository root, Python 3.12 or newer is sufficient; the demo uses only the standard library.

```bash
python -m case_studies.retail_telemetry --output artifacts/telemetry
```

Output is `artifacts/telemetry/report.json`. Regression checks:

```bash
python -m pip install -r requirements-offline.txt
python -m pytest offline_tests/test_case_studies.py -q
```

The fixed report contains five sessions, eight distinct payment attempts, two retry recoveries, one authorization-review candidate and one printer-failure session. One routine API call is retained in source event counts and excluded from incident flags.

## Contracts and failure cases

- **Event ID:** identical replay is ignored; conflicting records under one ID fail.
- **Attempt ID:** the same attempt in another event envelope contributes one payment attempt. Contradictory attempt records fail.
- **Authorization ID:** repeated observation of the same authorization does not create another distinct authorization. One authorization assigned to different sessions fails for reconciliation.
- **Session ID:** unique, explicit parent identity. Orphan events and events outside the session's inclusive start/end interval fail.
- **Time:** ISO seconds with an explicit offset, at most six fractional digits and valid offset minutes. Instants normalize to UTC; the demonstrated calendar partitions are UTC partitions.
- **Outcome:** payment approval/decline/error must be supplied. An approval requires an authorization reference; a failure cannot carry one.
- **Recovery chronology:** a failed attempt must precede a later approval. Success followed by failure, or equal timestamps with unresolved order, does not establish retry recovery. Source row order does not substitute for event time.

Tests cover replay, conflicting IDs, shared authorizations, missing authorization evidence, invalid time/offset/precision, out-of-window events and both midnight partitions.

## What this does and does not establish

Multiple authorizations are a review signal. They do not prove settlement, duplicate charging or financial loss: a session might contain legitimate multiple purchases, reversals or voids. The fixture has no settlement or transaction-amount feed.

Routine API duration is not used as an incident classifier. A missing event stream is not proof of a healthy site. Checkout completion, payment evidence and printer status remain separate fields.

This is an executable modeling case, not a production monitoring service. Streaming ingestion, late-event reopening, local-business timezone policy, device correlation, alert thresholds and provider reconciliation would need separate designs. Explicit session boundaries simplify the example; no heuristic sessionization quality is claimed.

[Return to the platform](../../README.md)
