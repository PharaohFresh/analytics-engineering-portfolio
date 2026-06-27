-- Date dimension built from the distinct dates that appear across order/fulfillment events.
-- Grain: one row per calendar date. (Phase 2: replace with a dbt_utils.date_spine for full coverage.)

with date_universe as (
    select order_date as calendar_date from {{ ref('stg_orders') }}
    union distinct
    select order_date from {{ ref('stg_order_items') }}
    union distinct
    select cast(shipped_at as date) from {{ ref('stg_order_items') }}
    union distinct
    select cast(delivered_at as date) from {{ ref('stg_order_items') }}
),

distinct_dates as (
    select distinct calendar_date
    from date_universe
    where calendar_date is not null
)

select
    calendar_date                                       as date_key,
    calendar_date,
    extract(year    from calendar_date)                 as year,
    extract(quarter from calendar_date)                 as quarter,
    extract(month   from calendar_date)                 as month,
    format_date('%B', calendar_date)                    as month_name,
    extract(day     from calendar_date)                 as day_of_month,
    extract(dayofweek from calendar_date)               as day_of_week,
    format_date('%a', calendar_date)                    as day_name,
    extract(dayofweek from calendar_date) in (1, 7)     as is_weekend
from distinct_dates
