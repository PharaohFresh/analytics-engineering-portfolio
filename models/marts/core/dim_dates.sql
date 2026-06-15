-- Date dimension built from the distinct dates that appear across order/line events.
-- Grain: one row per calendar date. (Phase 2: replace with a dbt_utils.date_spine for full coverage.)

with date_universe as (
    select order_date as calendar_date from {{ ref('stg_orders') }}
    union
    select ship_date    from {{ ref('stg_lineitems') }}
    union
    select commit_date  from {{ ref('stg_lineitems') }}
    union
    select receipt_date from {{ ref('stg_lineitems') }}
),

distinct_dates as (
    select distinct calendar_date
    from date_universe
    where calendar_date is not null
)

select
    calendar_date                                   as date_key,
    calendar_date,
    extract(year    from calendar_date)             as year,
    extract(quarter from calendar_date)             as quarter,
    extract(month   from calendar_date)             as month,
    to_char(calendar_date, 'MMMM')                  as month_name,
    extract(day     from calendar_date)             as day_of_month,
    extract(dayofweek from calendar_date)           as day_of_week,
    to_char(calendar_date, 'DY')                    as day_name,
    case when extract(dayofweek from calendar_date) in (0, 6)
         then true else false end                   as is_weekend
from distinct_dates
