with expected as (
    select count(*) as units, coalesce(sum(sale_price), 0) as revenue,
           coalesce(sum(gross_margin), 0) as margin,
           coalesce(sum(case when is_returned then 1 else 0 end), 0) as returned
    from {{ ref('fct_order_items') }}
), actual as (
    select coalesce(sum(units_sold), 0) as units, coalesce(sum(total_revenue), 0) as revenue,
           coalesce(sum(total_gross_margin), 0) as margin,
           coalesce(sum(units_returned), 0) as returned
    from {{ ref('mart_product_category_margin') }}
)
select expected.units as expected_units, actual.units as actual_units
from expected cross join actual
where expected.units != actual.units or expected.returned != actual.returned
   or abs(expected.revenue - actual.revenue) > greatest(0.000001, abs(expected.revenue) * 0.000000001)
   or abs(expected.margin - actual.margin) > greatest(0.000001, abs(expected.margin) * 0.000000001)
