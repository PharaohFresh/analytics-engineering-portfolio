with source as (
    select * from {{ source('thelook', 'products') }}
)

select
    id                          as product_key,
    name                        as product_name,
    brand,
    category,
    department,
    sku,
    cost,
    retail_price,
    distribution_center_id      as distribution_center_key
from source
