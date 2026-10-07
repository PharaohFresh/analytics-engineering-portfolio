-- Empty result means grain, plan uniqueness, sign and gross/return identity hold.
select 'duplicate_mart' as failure from {{ ref('mart_fiscal_attainment') }}
group by month_start, department having count(*) != 1
union all
select 'duplicate_target' from {{ ref('demo_fiscal_targets') }}
group by month_start, department having count(*) != 1
union all
select 'negative_target' from {{ ref('demo_fiscal_targets') }} where target_cents < 0
union all
select 'value_identity' from {{ ref('mart_fiscal_attainment') }}
where gross_value_cents - returned_value_cents != retained_value_cents
   or returned_units > units or returned_units < 0
