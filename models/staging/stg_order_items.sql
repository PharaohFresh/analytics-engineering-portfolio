with source as (
    select * from {{ source('thelook', 'order_items') }}
)

select
    id                  as order_item_key,
    order_id            as order_key,
    user_id             as customer_key,
    product_id          as product_key,
    inventory_item_id,
    status              as item_status,
    sale_price,
    created_at          as item_created_at,
    cast(created_at as date) as order_date,
    shipped_at,
    delivered_at,
    returned_at
from source
