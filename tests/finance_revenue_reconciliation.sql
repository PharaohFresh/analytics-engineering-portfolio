-- These sample prices are floating-point values, so use an explicit tolerance.
with expected as (
    select coalesce(sum(sale_price), 0) as revenue,
           coalesce(sum(gross_margin), 0) as margin
    from {{ ref('fct_order_items') }}
), actual as (
    select coalesce(sum(total_revenue), 0) as revenue,
           coalesce(sum(total_gross_margin), 0) as margin
    from {{ ref('mart_revenue_by_segment') }}
)
select expected.revenue as expected_revenue, actual.revenue as actual_revenue
from expected cross join actual
where abs(expected.revenue - actual.revenue) > greatest(0.000001, abs(expected.revenue) * 0.000000001)
   or abs(expected.margin - actual.margin) > greatest(0.000001, abs(expected.margin) * 0.000000001)
