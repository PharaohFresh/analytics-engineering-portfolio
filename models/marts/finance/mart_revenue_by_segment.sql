-- Business mart: net revenue and order metrics by customer market segment and region.
-- Grain: one row per (market_segment, region_name).

with order_items as (
    select * from {{ ref('fct_order_items') }}
),

customers as (
    select customer_key, market_segment, region_name
    from {{ ref('dim_customers') }}
)

select
    c.market_segment,
    c.region_name,
    count(distinct oi.order_key)    as order_count,
    sum(oi.quantity)                as total_quantity,
    sum(oi.net_revenue)             as total_net_revenue,
    round(sum(oi.net_revenue) / nullif(count(distinct oi.order_key), 0), 2) as avg_order_value
from order_items oi
inner join customers c on oi.customer_key = c.customer_key
group by c.market_segment, c.region_name
