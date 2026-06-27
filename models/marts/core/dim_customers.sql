-- Conformed customer dimension: customer attributes + inline geography + lifetime order summary.
-- Grain: one row per customer.

with customers as (
    select * from {{ ref('stg_customers') }}
),

customer_orders as (
    select * from {{ ref('int_customer_orders') }}
)

select
    c.customer_key,
    c.first_name,
    c.last_name,
    c.email,
    c.age,
    c.gender,
    c.city,
    c.state,
    c.postal_code,
    c.country,
    c.traffic_source,
    c.customer_created_at,
    co.lifetime_order_count,
    co.lifetime_units,
    co.lifetime_order_value,
    co.first_order_date,
    co.most_recent_order_date
from customers c
left join customer_orders co on c.customer_key = co.customer_key
