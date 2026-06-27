-- One row per order line (one physical unit), enriched with order, product, and
-- fulfillment context. Grain: order item. Feeds fct_order_items.

with order_items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select order_key, order_status
    from {{ ref('stg_orders') }}
),

products as (
    select
        product_key,
        product_name,
        brand,
        category,
        department,
        cost,
        retail_price,
        distribution_center_key
    from {{ ref('stg_products') }}
),

distribution_centers as (
    select distribution_center_key, distribution_center_name
    from {{ ref('stg_distribution_centers') }}
)

select
    oi.order_item_key,
    oi.order_key,
    oi.customer_key,
    oi.product_key,
    p.product_name,
    p.brand,
    p.category,
    p.department,
    p.distribution_center_key,
    dc.distribution_center_name,
    o.order_status,
    oi.item_status,
    oi.order_date,
    oi.item_created_at,
    oi.shipped_at,
    oi.delivered_at,
    oi.returned_at,
    oi.sale_price,
    p.cost                              as unit_cost,
    oi.sale_price - p.cost             as gross_margin,
    (oi.returned_at is not null)        as is_returned
from order_items oi
inner join orders o                 on oi.order_key = o.order_key
left join products p                on oi.product_key = p.product_key
left join distribution_centers dc   on p.distribution_center_key = dc.distribution_center_key
