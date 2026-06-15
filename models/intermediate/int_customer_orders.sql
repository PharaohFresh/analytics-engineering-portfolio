-- One row per customer with order-level aggregates. Feeds dim_customers enrichment / finance marts.
-- Grain: customer.

with orders as (
    select * from {{ ref('stg_orders') }}
)

select
    customer_key,
    count(*)                as lifetime_order_count,
    sum(total_price)        as lifetime_order_value,
    min(order_date)         as first_order_date,
    max(order_date)         as most_recent_order_date
from orders
group by customer_key
