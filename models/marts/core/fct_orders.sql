-- Order fact. Grain: one row per order.
-- Order-header price from source, plus line-rollup measures for reconciliation.

with orders as (
    select * from {{ ref('stg_orders') }}
),

line_rollup as (
    select
        order_key,
        count(*)            as line_count,
        sum(quantity)       as total_quantity,
        sum(net_revenue)    as total_net_revenue
    from {{ ref('stg_lineitems') }}
    group by order_key
)

select
    o.order_key,
    o.customer_key,
    o.order_date,
    o.order_status,
    o.order_priority,
    o.total_price          as order_header_price,
    lr.line_count,
    lr.total_quantity,
    lr.total_net_revenue
from orders o
left join line_rollup lr on o.order_key = lr.order_key
