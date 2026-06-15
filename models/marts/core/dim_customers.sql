-- Conformed customer dimension: customer attributes + geography + lifetime order summary.
-- Grain: one row per customer.

with customers as (
    select * from {{ ref('stg_customers') }}
),

nation as (
    select * from {{ ref('stg_nation') }}
),

region as (
    select * from {{ ref('stg_region') }}
),

customer_orders as (
    select * from {{ ref('int_customer_orders') }}
)

select
    c.customer_key,
    c.customer_name,
    c.market_segment,
    c.account_balance,
    n.nation_name,
    r.region_name,
    co.lifetime_order_count,
    co.lifetime_order_value,
    co.first_order_date,
    co.most_recent_order_date
from customers c
left join nation n          on c.nation_key = n.nation_key
left join region r          on n.region_key = r.region_key
left join customer_orders co on c.customer_key = co.customer_key
