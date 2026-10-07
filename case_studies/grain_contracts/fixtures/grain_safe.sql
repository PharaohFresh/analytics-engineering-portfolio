WITH design_counts AS (
    SELECT item_id, COUNT(*) AS customization_count
    FROM customizations
    GROUP BY item_id
)
SELECT i.item_id, i.order_id, i.sale_cents,
       COALESCE(p.category, 'Unmapped') AS category,
       COALESCE(d.customization_count, 0) AS customization_count
FROM physical_items i
LEFT JOIN products p ON i.product_id = p.product_id
LEFT JOIN design_counts d ON i.item_id = d.item_id
