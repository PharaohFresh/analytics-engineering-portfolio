-- Business mart: revenue and order metrics by acquisition channel and customer country.
-- Grain: one row per (traffic_source, country).

with order_items as (
    select * from {{ ref('fct_order_items') }}
),

customers as (
    select customer_key, traffic_source, country
    from {{ ref('dim_customers') }}
)

select
    c.traffic_source,
    c.country,
    count(distinct oi.order_key)        as order_count,
    count(*)                            as units_sold,
    sum(oi.sale_price)                  as total_revenue,
    sum(oi.gross_margin)                as total_gross_margin,
    round(sum(oi.sale_price) / nullif(count(distinct oi.order_key), 0), 2) as avg_order_value
from order_items oi
inner join customers c on oi.customer_key = c.customer_key
group by c.traffic_source, c.country
