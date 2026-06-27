-- One row per customer with order-level aggregates. Feeds dim_customers enrichment / finance marts.
-- Grain: customer. Revenue is rolled up from order items (orders carry no header price).

with order_items as (
    select * from {{ ref('stg_order_items') }}
)

select
    customer_key,
    count(distinct order_key)   as lifetime_order_count,
    count(*)                    as lifetime_units,
    sum(sale_price)             as lifetime_order_value,
    min(order_date)             as first_order_date,
    max(order_date)             as most_recent_order_date
from order_items
group by customer_key
