with source as (
    select * from {{ source('thelook', 'users') }}
)

select
    id              as customer_key,
    first_name,
    last_name,
    email,
    age,
    gender,
    city,
    state,
    postal_code,
    country,
    traffic_source,
    created_at      as customer_created_at
from source
