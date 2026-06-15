-- Business mart: spend and volume by supplier and supplier nation.
-- Grain: one row per supplier.

with order_items as (
    select * from {{ ref('fct_order_items') }}
),

suppliers as (
    select supplier_key, supplier_name, nation_name
    from {{ ref('dim_suppliers') }}
)

select
    s.supplier_key,
    s.supplier_name,
    s.nation_name,
    count(distinct oi.order_key)    as order_count,
    sum(oi.quantity)                as total_quantity,
    sum(oi.net_revenue)             as total_spend
from order_items oi
inner join suppliers s on oi.supplier_key = s.supplier_key
group by s.supplier_key, s.supplier_name, s.nation_name
