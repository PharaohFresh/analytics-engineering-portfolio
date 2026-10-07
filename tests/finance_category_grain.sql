-- Singular test: one row for each department/category combination.
select department, category
from {{ ref('mart_product_category_margin') }}
group by department, category
having count(*) > 1
