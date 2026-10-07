"""BigQuery read-only contracts, separate from API/authentication code."""
from __future__ import annotations

import re


def queries(project: str, dataset: str) -> list[tuple[str, str]]:
    if not re.fullmatch(r"[a-z][a-z0-9-]*", project) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", dataset):
        raise ValueError("Use a plain GCP project ID and BigQuery dataset identifier.")

    def table(name):
        return f"`{project}.{dataset}.{name}`"

    items, source, products = table("fct_order_items"), table("stg_order_items"), table("stg_products")
    orders, source_orders = table("fct_orders"), table("stg_orders")
    result = [
        ("item count matches source", f"SELECT (SELECT COUNT(*) FROM {items}) - (SELECT COUNT(*) FROM {source})"),
        ("order count matches source", f"SELECT (SELECT COUNT(*) FROM {orders}) - (SELECT COUNT(*) FROM {source_orders})"),
        ("items have parent orders", f"SELECT COUNT(*) FROM {items} i LEFT JOIN {orders} o USING(order_key) WHERE o.order_key IS NULL"),
        ("item prices are present", f"SELECT COUNT(*) FROM {items} WHERE sale_price IS NULL"),
    ]
    for relation, source_relation, key, label in [(items, source, "order_item_key", "item"), (orders, source_orders, "order_key", "order")]:
        result.extend([
            (f"{label} keys are unique", f"SELECT COUNT(*) FROM (SELECT {key} FROM {relation} GROUP BY {key} HAVING COUNT(*) > 1)"),
            (f"{label} keys are non-null", f"SELECT COUNT(*) FROM {relation} WHERE {key} IS NULL"),
            (f"{label} key sets match source", f"SELECT COUNT(*) FROM {relation} a FULL OUTER JOIN {source_relation} b USING({key}) WHERE a.{key} IS NULL OR b.{key} IS NULL"),
        ])
    comparisons = [f"i.{column} IS DISTINCT FROM s.{column}" for column in (
        "order_key", "customer_key", "product_key", "item_status", "sale_price", "item_created_at",
        "order_date", "shipped_at", "delivered_at", "returned_at",
    )]
    comparisons += ["i.unit_cost IS DISTINCT FROM p.cost", "i.category IS DISTINCT FROM p.category",
                    "i.department IS DISTINCT FROM p.department",
                    "i.distribution_center_key IS DISTINCT FROM p.distribution_center_key",
                    "i.gross_margin IS DISTINCT FROM (s.sale_price - p.cost)",
                    "i.is_returned IS DISTINCT FROM (s.returned_at IS NOT NULL)"]
    result.append(("item values and parent assignments match source by key",
                   f"SELECT COUNT(*) FROM {items} i JOIN {source} s USING(order_item_key) "
                   f"LEFT JOIN {products} p ON s.product_key = p.product_key WHERE " + " OR ".join(comparisons)))
    return result
