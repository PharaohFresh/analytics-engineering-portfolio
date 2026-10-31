-- Keyed reconciliation: every (traffic_source, country) bucket must match a recomputation from
-- the item fact, so mislabeled buckets or offsetting errors cannot hide behind a correct total.
-- Keys are coalesced so a null segment still joins; float totals use the explicit tolerance.
-- The rounded average allows one rounding step, because float sums can vary with summation order.
with expected as (
    select coalesce(c.traffic_source, '(null)') as traffic_source_key,
           coalesce(c.country, '(null)') as country_key,
           count(distinct oi.order_key) as order_count,
           count(*) as units_sold,
           sum(oi.sale_price) as total_revenue,
           sum(oi.gross_margin) as total_gross_margin
    from {{ ref('fct_order_items') }} oi
    inner join {{ ref('dim_customers') }} c on oi.customer_key = c.customer_key
    group by 1, 2
), actual as (
    select coalesce(traffic_source, '(null)') as traffic_source_key,
           coalesce(country, '(null)') as country_key,
           order_count, units_sold, total_revenue, total_gross_margin, avg_order_value
    from {{ ref('mart_revenue_by_segment') }}
)
select traffic_source_key, country_key
from expected e
full outer join actual a using (traffic_source_key, country_key)
where e.units_sold is null or a.units_sold is null
   or e.order_count is distinct from a.order_count
   or e.units_sold is distinct from a.units_sold
   or a.total_revenue is null
   or abs(e.total_revenue - a.total_revenue) > greatest(0.000001, abs(e.total_revenue) * 0.000000001)
   or (e.total_gross_margin is null) != (a.total_gross_margin is null)
   or abs(e.total_gross_margin - a.total_gross_margin) > greatest(0.000001, abs(e.total_gross_margin) * 0.000000001)
   or a.avg_order_value is null
   or abs(a.avg_order_value - round(e.total_revenue / e.order_count, 2)) > 0.011
