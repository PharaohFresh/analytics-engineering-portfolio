-- Distribution center (fulfillment origin) dimension. Grain: one row per center.

select
    distribution_center_key,
    distribution_center_name,
    latitude,
    longitude
from {{ ref('stg_distribution_centers') }}
