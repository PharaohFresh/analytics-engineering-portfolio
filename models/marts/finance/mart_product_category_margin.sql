-- Business mart: revenue, margin, and return rate by product category and department.
-- Grain: one row per (department, category).

with order_items as (
    select * from {{ ref('fct_order_items') }}
)

select
    department,
    category,
    count(*)                                                    as units_sold,
    sum(sale_price)                                             as total_revenue,
    sum(gross_margin)                                           as total_gross_margin,
    round(sum(gross_margin) / nullif(sum(sale_price), 0), 4)    as gross_margin_pct,
    sum(case when is_returned then 1 else 0 end)                as units_returned,
    round(sum(case when is_returned then 1 else 0 end) / nullif(count(*), 0), 4) as return_rate
from order_items
group by department, category
