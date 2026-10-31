{% snapshot snap_products %}
{{
    config(
        schema='snapshots',
        unique_key='product_key',
        strategy='check',
        check_cols=['retail_price', 'category', 'department']
    )
}}

-- SCD-2 history on product attributes that drift over time (price, category, department).
-- A suffixed schema, not a fixed dataset, gives each target its own <dataset>_snapshots history.
select
    product_key,
    product_name,
    category,
    department,
    cost,
    retail_price
from {{ ref('stg_products') }}

{% endsnapshot %}
