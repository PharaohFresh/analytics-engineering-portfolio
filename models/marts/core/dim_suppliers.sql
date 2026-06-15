-- Supplier dimension with geography. Grain: one row per supplier.

with suppliers as (
    select * from {{ ref('stg_suppliers') }}
),

nation as (
    select * from {{ ref('stg_nation') }}
),

region as (
    select * from {{ ref('stg_region') }}
)

select
    s.supplier_key,
    s.supplier_name,
    s.account_balance,
    n.nation_name,
    r.region_name
from suppliers s
left join nation n on s.nation_key = n.nation_key
left join region r on n.region_key = r.region_key
