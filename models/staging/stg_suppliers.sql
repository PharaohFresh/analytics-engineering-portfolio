with source as (
    select * from {{ source('tpch', 'supplier') }}
)

select
    s_suppkey   as supplier_key,
    s_name      as supplier_name,
    s_address   as address,
    s_nationkey as nation_key,
    s_phone     as phone,
    s_acctbal   as account_balance
from source
