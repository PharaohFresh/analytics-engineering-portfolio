-- Keyed reconciliation: every (department, category) bucket must match a recomputation from
-- the item fact, including its ratios, so offsetting errors cannot hide behind a correct total.
-- Keys are coalesced so a null category still joins; float totals use the explicit tolerance.
-- Rounded ratios allow one rounding step, because float sums can vary with summation order.
with expected as (
    select coalesce(department, '(null)') as department_key,
           coalesce(category, '(null)') as category_key,
           count(*) as units_sold,
           sum(sale_price) as total_revenue,
           sum(gross_margin) as total_gross_margin,
           sum(case when is_returned then 1 else 0 end) as units_returned
    from {{ ref('fct_order_items') }}
    group by 1, 2
), actual as (
    select coalesce(department, '(null)') as department_key,
           coalesce(category, '(null)') as category_key,
           units_sold, total_revenue, total_gross_margin, gross_margin_pct, units_returned, return_rate
    from {{ ref('mart_product_category_margin') }}
)
select department_key, category_key
from expected e
full outer join actual a using (department_key, category_key)
where e.units_sold is null or a.units_sold is null
   or e.units_sold is distinct from a.units_sold
   or e.units_returned is distinct from a.units_returned
   or a.total_revenue is null
   or abs(e.total_revenue - a.total_revenue) > greatest(0.000001, abs(e.total_revenue) * 0.000000001)
   or (e.total_gross_margin is null) != (a.total_gross_margin is null)
   or abs(e.total_gross_margin - a.total_gross_margin) > greatest(0.000001, abs(e.total_gross_margin) * 0.000000001)
   or (a.gross_margin_pct is null) != (e.total_gross_margin is null or e.total_revenue = 0)
   or abs(a.gross_margin_pct - round(e.total_gross_margin / nullif(e.total_revenue, 0), 4)) > 0.00011
   or a.return_rate is null
   or abs(a.return_rate - round(e.units_returned / e.units_sold, 4)) > 0.00011
