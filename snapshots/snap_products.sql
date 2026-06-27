{% snapshot snap_products %}
{{
    config(
        target_schema='snapshots',
        unique_key='product_key',
        strategy='check',
        check_cols=['retail_price', 'category', 'department']
    )
}}

-- SCD-2 history on product attributes that drift over time (price, category, department).
select
    product_key,
    product_name,
    category,
    department,
    cost,
    retail_price
from {{ ref('stg_products') }}

{% endsnapshot %}
