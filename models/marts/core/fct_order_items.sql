{{
    config(
        materialized='incremental',
        unique_key='order_item_key',
        incremental_strategy='merge'
    )
}}

-- Order-line fact. Grain: one row per order line (order_key + line_number).
-- Incremental on order_date to mirror high-volume transactional fact patterns.

with enriched as (
    select * from {{ ref('int_order_items_enriched') }}
)

select
    order_key || '-' || line_number as order_item_key,
    order_key,
    line_number,
    customer_key,
    part_key,
    supplier_key,
    order_date,
    ship_date,
    ship_mode,
    return_flag,
    quantity,
    extended_price,
    discount,
    tax,
    net_revenue
from enriched

{% if is_incremental() %}
-- only process orders newer than what's already loaded
where order_date > (select coalesce(max(order_date), '1900-01-01') from {{ this }})
{% endif %}
