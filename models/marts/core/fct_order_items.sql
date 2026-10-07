{{
    config(
        materialized='incremental',
        unique_key='order_item_key',
        incremental_strategy='merge'
    )
}}

-- Order-item fact. Grain: one row per order item (one physical unit).
-- Merge all current source rows: creation time is not a reliable change watermark.
-- This deliberately trades source-scan efficiency for correct mutable item state.
-- Late arrivals, timestamp ties, returns and current product enrichment all update.
-- Landmine: thelook_ecommerce is periodically regenerated upstream (keys reassigned),
-- so rows merged from a prior generation become orphans vs. the rebuilt fct_orders.
-- The relationships test catches it; recovery is `dbt build --full-refresh`.

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
