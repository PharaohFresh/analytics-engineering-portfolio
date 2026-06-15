-- One row per order line, enriched with order context, part, and supplier attributes.
-- Grain: order line (order_key + line_number). Feeds fct_order_items.

with lineitems as (
    select * from {{ ref('stg_lineitems') }}
),

orders as (
    select order_key, customer_key, order_date, order_status
    from {{ ref('stg_orders') }}
),

parts as (
    select part_key, brand, manufacturer, part_type
    from {{ ref('stg_parts') }}
),

suppliers as (
    select supplier_key, supplier_name, nation_key as supplier_nation_key
    from {{ ref('stg_suppliers') }}
)

select
    li.order_key,
    li.line_number,
    o.customer_key,
    o.order_date,
    o.order_status,
    li.part_key,
    p.brand,
    p.manufacturer,
    p.part_type,
    li.supplier_key,
    s.supplier_name,
    s.supplier_nation_key,
    li.quantity,
    li.extended_price,
    li.discount,
    li.tax,
    li.net_revenue,
    li.return_flag,
    li.ship_date,
    li.ship_mode
from lineitems li
inner join orders o     on li.order_key = o.order_key
left join parts p       on li.part_key = p.part_key
left join suppliers s   on li.supplier_key = s.supplier_key
