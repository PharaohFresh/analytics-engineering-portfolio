{% snapshot snap_suppliers %}
{{
    config(
        target_schema='snapshots',
        unique_key='supplier_key',
        strategy='check',
        check_cols=['account_balance', 'supplier_name']
    )
}}

-- SCD-2 history on supplier attributes that drift over time (e.g., account balance).
select
    supplier_key,
    supplier_name,
    nation_key,
    account_balance
from {{ ref('stg_suppliers') }}

{% endsnapshot %}
