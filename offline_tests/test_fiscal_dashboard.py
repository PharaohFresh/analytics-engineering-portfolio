from copy import deepcopy
import json
from pathlib import Path

import pytest

from case_studies.fiscal_attainment.__main__ import FIELDS, aggregate, build, reconcile, targets

FIXTURE = Path(__file__).resolve().parents[1] / 'case_studies/fiscal_attainment/fixtures/items.json'


def items():
    return json.loads(FIXTURE.read_text(encoding='utf-8'))


def test_exact_grain_totals_and_unmapped_preservation():
    rows = aggregate(items(), targets())
    assert len(rows) == 9
    assert sum(r['gross_value_cents'] for r in rows) == 97000
    assert sum(r['retained_value_cents'] for r in rows) == 89000
    assert sum(r['returned_value_cents'] for r in rows) == 8000
    assert sum(r['indicative_margin_cents'] for r in rows) == 49000
    assert sum(r['units'] for r in rows) == 7
    assert sum(r['returned_units'] for r in rows) == 1


def test_zero_and_missing_plan_are_distinct_and_empty_month_retained():
    rows = {(r['month_start'], r['department']): r for r in aggregate(items(), targets())}
    assert rows['2026-04-01', 'Women']['target_cents'] == 0
    assert rows['2026-04-01', 'Unmapped']['target_cents'] is None
    assert rows['2026-03-01', 'Women']['retained_value_cents'] == 0
    assert rows['2026-03-01', 'Women']['target_cents'] == 18000


def test_exact_period_boundaries_and_cancelled_exclusion():
    changed = items()
    changed[-1]['price_cents'] = 999999
    changed[4]['price_cents'] = 999999
    assert aggregate(changed, targets()) == aggregate(items(), targets())


def test_public_and_offline_plans_preserve_the_same_coverage_contract():
    small = {(r['month_start'],r['department']):r['target_cents'] for r in targets()}
    public = {(r['month_start'],r['department']):r['target_cents'] for r in targets(warehouse=True)}
    assert set(small) == set(public)
    assert public == {key:value*1000 for key,value in small.items()}


def test_old_return_restates_the_correct_month():
    changed = items()
    changed[0]['is_returned'] = True
    rows = aggregate(changed, targets())
    assert sum(r['retained_value_cents'] for r in rows) == 79000
    feb = next(r for r in rows if r['month_start'] == '2026-02-01' and r['department'] == 'Men')
    assert feb['returned_value_cents'] == 18000
    assert feb['retained_value_cents'] == 0


@pytest.mark.parametrize('mutate', [
    lambda x: x.append(deepcopy(x[0])),
    lambda x: x[0].update(price_cents=True),
    lambda x: x[0].update(cost_cents=None),
    lambda x: x[0].update(item_status='Surprise'),
    lambda x: x[0].update(is_returned=1),
    lambda x: x[0].update(order_date='2026-02-30'),
    lambda x: x[1].update(is_returned=False),
])
def test_ambiguous_items_fail(mutate):
    changed = items()
    mutate(changed)
    with pytest.raises(ValueError):
        aggregate(changed, targets())


def test_duplicate_negative_and_boolean_targets_fail():
    for value in (-1, True):
        plans = targets()
        plans[0]['target_cents'] = value
        with pytest.raises(ValueError):
            aggregate(items(), plans)
    with pytest.raises(ValueError):
        aggregate(items(), targets() + [targets()[0]])


@pytest.mark.parametrize('corruption', ['duplicate', 'drop', 'value', 'move'])
def test_same_count_or_coverage_corruption_blocks_publication(corruption):
    rows = aggregate(items(), targets())
    observed = deepcopy(rows)
    if corruption == 'duplicate':
        observed[-1] = deepcopy(observed[0])
    elif corruption == 'drop':
        observed.pop()
    elif corruption == 'value':
        observed[0]['retained_value_cents'] += 1
    else:
        observed[0]['department'] = 'Another department'
    with pytest.raises(ValueError):
        reconcile(rows, observed)


def test_safe_static_output_and_completed_evidence_not_overwritten(tmp_path):
    report = build(tmp_path / 'dashboard')
    assert len(report['rows']) == 9
    html = (tmp_path / 'dashboard/index.html').read_text(encoding='utf-8')
    assert '__DASHBOARD_DATA__' not in html
    assert 'Original invented items' in html
    with pytest.raises(FileExistsError):
        build(tmp_path / 'dashboard')
