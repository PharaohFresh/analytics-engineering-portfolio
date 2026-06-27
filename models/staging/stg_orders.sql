with source as (
    select * from {{ source('thelook', 'orders') }}
)

select
    order_id            as order_key,
    user_id             as customer_key,
    status              as order_status,
    num_of_item         as num_items,
    created_at          as order_created_at,
    cast(created_at as date) as order_date,
    shipped_at,
    delivered_at,
    returned_at
from source
