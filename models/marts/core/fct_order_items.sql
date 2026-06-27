{{
    config(
        materialized='incremental',
        unique_key='order_item_key',
        incremental_strategy='merge'
    )
}}

-- Order-item fact. Grain: one row per order item (one physical unit).
-- Incremental on item_created_at to mirror high-volume transactional fact patterns.

with enriched as (
    select * from {{ ref('int_order_items_enriched') }}
)

select
    order_item_key,
    order_key,
    customer_key,
    product_key,
    category,
    department,
    distribution_center_key,
    item_status,
    order_date,
    item_created_at,
    shipped_at,
    delivered_at,
    returned_at,
    is_returned,
    sale_price,
    unit_cost,
    gross_margin
from enriched

{% if is_incremental() %}
-- only process items newer than what's already loaded
where item_created_at > (select coalesce(max(item_created_at), timestamp '1900-01-01') from {{ this }})
{% endif %}
