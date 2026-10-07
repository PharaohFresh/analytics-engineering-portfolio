import copy
import json

import pytest

from case_studies.grain_contracts import GrainError, connection, evaluate as grain
from case_studies.retail_telemetry import FIXTURE, TelemetryError, evaluate as telemetry, instant


def fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_customization_preaggregation_keeps_physical_units_and_money():
    report=grain()
    assert report['correct']=={'orders':3,'physical_units':5,'revenue_cents':50000,'customization_records':7,'unmapped_product_units':1}
    assert report['naive_customization_join']=={'rows':8,'revenue_cents':85000}
    assert report['inner_product_join']['revenue_cents']==38000


@pytest.mark.parametrize('mutation',[
 "INSERT INTO physical_items SELECT * FROM physical_items WHERE item_id='item-one'",
 "UPDATE physical_items SET order_id='unknown' WHERE item_id='item-one'",
 "UPDATE physical_items SET item_id=NULL WHERE item_id='item-one'",
 "UPDATE physical_items SET sale_cents=1.5 WHERE item_id='item-one'",
 "INSERT INTO products SELECT * FROM products WHERE product_id='mug'",
 "UPDATE customizations SET item_id='unknown' WHERE customization_id='design-one'",
])
def test_grain_contracts_detect_bad_source_keys_and_amounts(mutation):
    conn=connection();conn.execute(mutation)
    with pytest.raises(GrainError):grain(conn)


def test_telemetry_distinguishes_retry_printer_and_authorization_review():
    report=telemetry();rows={x['session_id']:x for x in report['sessions']}
    assert report['summary']=={'sessions':5,'unique_events':15,'payment_attempts':8,
                              'recovered_retry_sessions':2,'authorization_review_candidates':1,
                              'printer_failure_sessions':1,'cross_midnight_sessions':1}
    assert rows['session-retry']['recovered_retry'] is True
    assert rows['session-retry']['authorization_review_candidate'] is False
    assert rows['session-review']['authorization_review_candidate'] is True
    assert rows['session-printer']['printer_failures']==1
    assert rows['session-normal']['authorization_review_candidate'] is False
    assert report['routine_api_calls_excluded_from_incident_flags']==1


def test_midnight_session_includes_authorization_in_next_partition():
    report=telemetry();row=next(x for x in report['sessions'] if x['session_id']=='session-midnight')
    assert row['distinct_authorizations']==1 and row['start_partition_authorizations']==0
    assert report['events_by_utc_partition']=={'2026-09-01':13,'2026-09-02':2}


@pytest.mark.parametrize('failed_at,approved_at,expected', [
 ('11:04','11:02',False), ('11:02','11:02',False), ('11:02','11:04',True)])
def test_retry_recovery_requires_a_strictly_later_approval(failed_at,approved_at,expected):
    payload=fixture()
    payload['events'][3]['occurred_at']=f'2026-09-01T{failed_at}:00Z'
    payload['events'][4]['occurred_at']=f'2026-09-01T{approved_at}:00Z'
    row=next(x for x in telemetry(payload)['sessions'] if x['session_id']=='session-retry')
    assert row['recovered_retry'] is expected


def test_source_row_order_does_not_determine_retry_chronology():
    payload=fixture();payload['events'].reverse()
    assert telemetry(payload)['summary']==telemetry()['summary']


def test_identical_event_replay_does_not_inflate_session_metrics():
    payload=fixture();payload['events']*=2;report=telemetry(payload)
    assert report['identical_event_records_ignored']==15
    assert report['summary']==telemetry()['summary']


def test_conflicting_replay_is_rejected():
    payload=fixture();other=copy.deepcopy(payload['events'][0]);other['duration_ms']=1;payload['events'].append(other)
    with pytest.raises(TelemetryError,match='conflicting source'):telemetry(payload)


def test_same_attempt_in_two_event_envelopes_is_not_another_payment():
    payload=fixture();other=copy.deepcopy(payload['events'][1]);other['event_id']='new-envelope';payload['events'].append(other)
    report=telemetry(payload)
    assert report['summary']['payment_attempts']==8 and report['duplicate_attempt_records_ignored']==1


def test_repeated_authorization_does_not_claim_a_second_charge():
    payload=fixture();other=copy.deepcopy(payload['events'][1])
    other.update(event_id='new-payment-event',attempt_id='new-attempt');payload['events'].append(other)
    report=telemetry(payload);normal=next(x for x in report['sessions'] if x['session_id']=='session-normal')
    assert normal['payment_attempts']==2 and normal['distinct_authorizations']==1
    assert normal['authorization_review_candidate'] is False


@pytest.mark.parametrize('mutation', ['unknown_session','outside_interval','naive_time','invalid_offset','no_authorization','unknown_kind','negative_duration','duplicate_session','shared_authorization','conflicting_attempt'])
def test_telemetry_rejects_unreconciled_input(mutation):
    payload=fixture()
    if mutation=='unknown_session':payload['events'][0]['session_id']='unknown'
    elif mutation=='outside_interval':payload['events'][0]['occurred_at']='2026-09-01T09:00:00Z'
    elif mutation=='naive_time':payload['events'][0]['occurred_at']='2026-09-01T10:01:00'
    elif mutation=='invalid_offset':payload['events'][0]['occurred_at']='2026-09-01T10:01:00+00:60'
    elif mutation=='no_authorization':payload['events'][1]['authorization_id']=None
    elif mutation=='unknown_kind':payload['events'][0]['kind']='guessed-incident'
    elif mutation=='negative_duration':payload['events'][0]['duration_ms']=-1
    elif mutation=='duplicate_session':payload['sessions'].append(dict(payload['sessions'][0]))
    elif mutation=='shared_authorization':payload['events'][4]['authorization_id']='auth-01'
    else:
        other=copy.deepcopy(payload['events'][1]);other.update(event_id='conflict',outcome='declined',authorization_id=None)
        payload['events'].append(other)
    with pytest.raises(TelemetryError):telemetry(payload)


def test_event_offset_normalization_and_unsupported_precision():
    assert instant('2026-09-01T09:00:00-05:00')==instant('2026-09-01T14:00:00Z')
    with pytest.raises(TelemetryError):instant('2026-09-01T09:00:00.0000001-05:00')
