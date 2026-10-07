from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MONTHS = ('2026-02-01', '2026-03-01', '2026-04-01')
FIELDS = ('gross_value_cents', 'returned_value_cents', 'retained_value_cents',
          'indicative_margin_cents', 'units', 'returned_units')
STATUSES = {'Complete', 'Shipped', 'Processing', 'Cancelled', 'Returned'}


def targets(*, warehouse=False):
    path = ROOT / 'seeds/demo_fiscal_targets.csv' if warehouse else Path(__file__).parent / 'fixtures/targets.csv'
    with path.open(encoding='utf-8', newline='') as stream:
        return [{**row, 'target_cents': int(row['target_cents'])} for row in csv.DictReader(stream)]


def aggregate(items, plans):
    """Preserve item grain, empty months and missing plans; fail on ambiguous inputs."""
    planned = {}
    for plan in plans:
        key = (plan['month_start'], plan['department'])
        if key in planned or key[0] not in MONTHS or not isinstance(key[1], str) or not key[1]:
            raise ValueError('Invalid or duplicate fiscal target key')
        if type(plan['target_cents']) is not int or plan['target_cents'] < 0:
            raise ValueError('Targets must be nonnegative integer cents')
        planned[key] = plan['target_cents']
    departments = {key[1] for key in planned}
    valid = []
    seen = set()
    for item in items:
        key = item['order_item_key']
        if type(key) is not int or key in seen:
            raise ValueError('Invalid or duplicate item key')
        seen.add(key)
        order_date = date.fromisoformat(item['order_date'])
        if order_date.isoformat() != item['order_date']:
            raise ValueError('Dates must use YYYY-MM-DD')
        if item['item_status'] not in STATUSES or type(item['is_returned']) is not bool:
            raise ValueError('Unknown item state')
        if item['item_status'] == 'Returned' and not item['is_returned']:
            raise ValueError('Returned status disagrees with return flag')
        for field in ('price_cents', 'cost_cents'):
            if type(item[field]) is not int or item[field] < 0:
                raise ValueError('Item money must be nonnegative integer cents')
        department = item['department']
        if department is not None and (not isinstance(department, str) or not department):
            raise ValueError('Invalid department')
        if '2026-02-01' <= item['order_date'] < '2026-05-01':
            departments.add(department or 'Unmapped')
            valid.append(item)
    buckets = {(month, dept): dict(month_start=month, department=dept, fiscal_year=2027,
                fiscal_month=int(month[5:7]) - 1, target_cents=planned.get((month, dept)),
                **{field: 0 for field in FIELDS}) for month in MONTHS for dept in sorted(departments)}
    for item in valid:
        if item['item_status'] == 'Cancelled':
            continue
        row = buckets[(item['order_date'][:7] + '-01', item['department'] or 'Unmapped')]
        row['gross_value_cents'] += item['price_cents']
        row['units'] += 1
        if item['is_returned']:
            row['returned_value_cents'] += item['price_cents']
            row['returned_units'] += 1
        else:
            row['retained_value_cents'] += item['price_cents']
            row['indicative_margin_cents'] += item['price_cents'] - item['cost_cents']
    return [buckets[key] for key in sorted(buckets)]


def reconcile(expected, observed):
    def keyed(rows):
        result = {}
        for row in rows:
            key = (str(row['month_start']), row['department'])
            if key in result:
                raise ValueError('Duplicate dashboard mart row')
            result[key] = {field: row[field] for field in (*FIELDS, 'target_cents', 'fiscal_year', 'fiscal_month')}
        return result
    if keyed(expected) != keyed(observed):
        raise ValueError('Warehouse/dashboard reconciliation failed: key or value differs')


def build(output, *, warehouse=False):
    if warehouse:
        from google.cloud import bigquery
        client = bigquery.Client(project='career-analytics-portfolio')
        table = '`career-analytics-portfolio.dbt_ci.fct_order_items`'
        sql = f'''SELECT order_item_key, order_key, department, CAST(order_date AS STRING) order_date,
            item_status, is_returned,
            CAST(ROUND(CAST(sale_price AS NUMERIC)*100) AS INT64) price_cents,
            CAST(ROUND(CAST(unit_cost AS NUMERIC)*100) AS INT64) cost_cents
            FROM {table} WHERE order_date >= DATE '2026-02-01' AND order_date < DATE '2026-05-01' '''
        config = bigquery.QueryJobConfig(maximum_bytes_billed=100_000_000, use_query_cache=False)
        items = [dict(row) for row in client.query(sql, job_config=config).result(timeout=120)]
        if not items:
            raise ValueError('Public warehouse cohort is empty; refuse misleading live dashboard')
        observed = [dict(row) for row in client.query(
            'SELECT * FROM `career-analytics-portfolio.dbt_ci.mart_fiscal_attainment`',
            job_config=config).result(timeout=120)]
        for row in observed:
            row['month_start'] = row['month_start'].isoformat()
        origin = 'Public theLook warehouse + invented planning targets'
    else:
        items = json.loads((Path(__file__).parent / 'fixtures/items.json').read_text(encoding='utf-8'))
        observed = None
        origin = 'Original invented items + invented planning targets'
    rows = aggregate(items, targets(warehouse=warehouse))
    if observed is not None:
        reconcile(rows, observed)
    report = dict(data_origin=origin, generated_at=datetime.now(timezone.utc).isoformat(),
                  period='2026-02-01 through 2026-04-30',
                  fiscal_convention='February start; FY2027 is named by ending year',
                  verification='Independent item-to-mart key/value reconciliation passed' if warehouse else 'Offline fixture contracts passed',
                  rows=rows)
    payload = json.dumps(report, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    template = (ROOT / 'dashboard/template.html').read_text(encoding='utf-8')
    output.mkdir(parents=True, exist_ok=False)
    (output / 'index.html').write_text(template.replace('__DASHBOARD_DATA__', payload), encoding='utf-8')
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'[OK] {len(rows)} fiscal buckets; {origin}; dashboard written to {output}')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build a reconciled fiscal dashboard without a server dependency')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--warehouse', action='store_true', help='Read only the personal dbt_ci target using supplied credentials')
    args = parser.parse_args()
    build(args.output, warehouse=args.warehouse)
