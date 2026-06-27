-- Product dimension with fulfillment origin. Grain: one row per product.

with products as (
    select * from {{ ref('stg_products') }}
),

distribution_centers as (
    select distribution_center_key, distribution_center_name
    from {{ ref('stg_distribution_centers') }}
)

select
    p.product_key,
    p.product_name,
    p.brand,
    p.category,
    p.department,
    p.sku,
    p.cost,
    p.retail_price,
    p.retail_price - p.cost              as list_margin,
    p.distribution_center_key,
    dc.distribution_center_name
from products p
left join distribution_centers dc on p.distribution_center_key = dc.distribution_center_key
