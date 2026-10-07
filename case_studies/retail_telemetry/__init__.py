from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re


FIXTURE = Path(__file__).parent / "fixtures" / "events.json"


class TelemetryError(ValueError):
    pass


def instant(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])", value):
        raise TelemetryError("Use ISO seconds with an explicit offset and at most six fractional digits.")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError as exc:
        raise TelemetryError("Invalid telemetry timestamp.") from exc


def required_id(record, key):
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise TelemetryError(f"A nonempty {key} is required.")
    return value


def evaluate(payload=None):
    payload = payload if payload is not None else json.loads(FIXTURE.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("sessions"), list) or not isinstance(payload.get("events"), list):
        raise TelemetryError("Expected explicit session and event lists.")
    sessions = {}
    for row in payload["sessions"]:
        if not isinstance(row, dict):
            raise TelemetryError("A session record must be an object.")
        sid = required_id(row, "session_id")
        required_id(row, "site")
        if sid in sessions:
            raise TelemetryError("Session IDs must be unique.")
        start, end = instant(row.get("started_at")), instant(row.get("ended_at"))
        if end <= start:
            raise TelemetryError("Session end must follow its start.")
        sessions[sid] = {**row, "start": start, "end": end}
    if not sessions:
        raise TelemetryError("An empty session list is not a healthy-site observation.")
    events, attempts, auth_owners = {}, {}, {}
    duplicate_events = duplicate_attempts = 0
    for row in payload["events"]:
        if not isinstance(row, dict):
            raise TelemetryError("An event record must be an object.")
        event_id = required_id(row, "event_id")
        sid = required_id(row, "session_id")
        if event_id in events:
            if events[event_id] != row:
                raise TelemetryError("One event ID has conflicting source records.")
            duplicate_events += 1
            continue
        if sid not in sessions:
            raise TelemetryError("Event refers to an unknown session.")
        occurred = instant(row.get("occurred_at"))
        if not sessions[sid]["start"] <= occurred <= sessions[sid]["end"]:
            raise TelemetryError("Event falls outside its declared session interval.")
        kind = row.get("kind")
        if kind not in {"payment_attempt", "checkout_completed", "printer_failure", "api_call"}:
            raise TelemetryError("Unsupported event kind.")
        if kind == "payment_attempt":
            attempt_id = required_id(row, "attempt_id")
            if row.get("outcome") not in {"approved", "declined", "error"}:
                raise TelemetryError("Payment outcome must be explicit.")
            auth = row.get("authorization_id")
            if row["outcome"] == "approved":
                required_id(row, "authorization_id")
                if auth in auth_owners and auth_owners[auth] != sid:
                    raise TelemetryError("An authorization is assigned to conflicting sessions.")
                auth_owners[auth] = sid
            elif auth is not None:
                raise TelemetryError("A failed attempt cannot supply a successful authorization.")
            identity = (sid, occurred, row["outcome"], auth)
            if attempt_id in attempts:
                if attempts[attempt_id] != identity:
                    raise TelemetryError("One payment attempt has conflicting records.")
                duplicate_attempts += 1
            else:
                attempts[attempt_id] = identity
        if kind == "api_call" and (not isinstance(row.get("duration_ms"), int) or isinstance(row["duration_ms"], bool) or row["duration_ms"] < 0):
            raise TelemetryError("API duration must be nonnegative integer milliseconds.")
        events[event_id] = row
    summaries = []
    for sid, session in sorted(sessions.items()):
        records = [row for row in events.values() if row["session_id"] == sid]
        payments = [row for row in attempts.values() if row[0] == sid]
        successful = {row[3] for row in payments if row[2] == "approved"}
        failed = sum(row[2] != "approved" for row in payments)
        failed_times = [row[1] for row in payments if row[2] != "approved"]
        approved_times = [row[1] for row in payments if row[2] == "approved"]
        recovered = bool(failed_times and approved_times and min(failed_times) < max(approved_times))
        summaries.append({
            "session_id": sid, "site": session["site"], "payment_attempts": len(payments),
            "distinct_authorizations": len(successful), "failed_attempts": failed,
            "recovered_retry": recovered,
            "authorization_review_candidate": len(successful) > 1,
            "printer_failures": sum(row["kind"] == "printer_failure" for row in records),
            "checkout_completed": any(row["kind"] == "checkout_completed" for row in records),
            "crosses_utc_midnight": session["start"].date() != session["end"].date(),
            "start_partition_authorizations": len({row[3] for row in payments if row[2] == "approved" and row[1].date() == session["start"].date()}),
        })
    partitions = Counter(instant(row["occurred_at"]).date().isoformat() for row in events.values())
    return {
        "data_origin": "invented sessions, event IDs and authorization references",
        "summary": {"sessions": len(summaries), "unique_events": len(events),
                    "payment_attempts": len(attempts), "recovered_retry_sessions": sum(x["recovered_retry"] for x in summaries),
                    "authorization_review_candidates": sum(x["authorization_review_candidate"] for x in summaries),
                    "printer_failure_sessions": sum(x["printer_failures"] > 0 for x in summaries),
                    "cross_midnight_sessions": sum(x["crosses_utc_midnight"] for x in summaries)},
        "events_by_utc_partition": dict(sorted(partitions.items())), "sessions": summaries,
        "identical_event_records_ignored": duplicate_events, "duplicate_attempt_records_ignored": duplicate_attempts,
        "routine_api_calls_excluded_from_incident_flags": sum(row["kind"] == "api_call" for row in events.values()),
        "limits": "Authorization candidates require settlement/provider review; no duplicate charge or financial loss proven.",
    }
