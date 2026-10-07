-- Demonstration fiscal calendar: February start, fiscal year named by ending year.
-- Fixed completed item-created cohort: February-April 2026. Targets are invented, not business budgets.
-- Grain: one row per (month_start, department), including empty and unplanned buckets.
with items as (
    select *,
        cast(round(cast(sale_price as numeric) * 100) as int64) as price_cents,
        cast(round(cast(unit_cost as numeric) * 100) as int64) as cost_cents
    from {{ ref('fct_order_items') }}
    where order_date >= date '2026-02-01' and order_date < date '2026-05-01'
),
actuals as (
    select date_trunc(order_date, month) as month_start,
        coalesce(department, 'Unmapped') as department,
        sum(case when item_status != 'Cancelled' then price_cents else 0 end) as gross_value_cents,
        sum(case when item_status != 'Cancelled' and is_returned then price_cents else 0 end) as returned_value_cents,
        sum(case when item_status != 'Cancelled' and not is_returned then price_cents else 0 end) as retained_value_cents,
        sum(case when item_status != 'Cancelled' and not is_returned then price_cents - cost_cents else 0 end) as indicative_margin_cents,
        countif(item_status != 'Cancelled') as units,
        countif(item_status != 'Cancelled' and is_returned) as returned_units
    from items group by 1, 2
),
departments as (
    select distinct department from actuals
    union distinct select department from {{ ref('demo_fiscal_targets') }}
),
spine as (
    select month_start, department
    from unnest(generate_date_array(date '2026-02-01', date '2026-04-01', interval 1 month)) as month_start
    cross join departments
)
select s.month_start, s.department,
    2027 as fiscal_year, extract(month from s.month_start) - 1 as fiscal_month,
    coalesce(a.gross_value_cents, 0) as gross_value_cents,
    coalesce(a.returned_value_cents, 0) as returned_value_cents,
    coalesce(a.retained_value_cents, 0) as retained_value_cents,
    coalesce(a.indicative_margin_cents, 0) as indicative_margin_cents,
    coalesce(a.units, 0) as units, coalesce(a.returned_units, 0) as returned_units,
    cast(t.target_cents as int64) as target_cents
from spine s
left join actuals a using (month_start, department)
left join {{ ref('demo_fiscal_targets') }} t using (month_start, department)
