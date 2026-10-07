-- Singular test: one row for each acquisition-channel/country combination.
select traffic_source, country
from {{ ref('mart_revenue_by_segment') }}
group by traffic_source, country
having count(*) > 1
