-- Order fact. Grain: one row per order.
-- Orders carry no header price in this source, so revenue/margin roll up from order items.

with orders as (
    select * from {{ ref('stg_orders') }}
),

line_rollup as (
    select
        order_key,
        count(*)                            as item_count,
        sum(sale_price)                     as total_revenue,
        sum(gross_margin)                   as total_gross_margin,
        sum(case when is_returned then 1 else 0 end) as returned_item_count
    from {{ ref('int_order_items_enriched') }}
    group by order_key
)

select
    o.order_key,
    o.customer_key,
    o.order_date,
    o.order_status,
    o.num_items,
    o.shipped_at,
    o.delivered_at,
    o.returned_at,
    lr.item_count,
    lr.total_revenue,
    lr.total_gross_margin,
    lr.returned_item_count
from orders o
left join line_rollup lr on o.order_key = lr.order_key
