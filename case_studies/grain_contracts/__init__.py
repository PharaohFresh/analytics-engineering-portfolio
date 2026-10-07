from __future__ import annotations

import sqlite3
from pathlib import Path


FIXTURES = Path(__file__).parent / "fixtures"


class GrainError(ValueError):
    pass


def connection():
    conn = sqlite3.connect(":memory:")
    conn.executescript((FIXTURES / "seed.sql").read_text(encoding="utf-8"))
    return conn


def evaluate(conn=None):
    own = conn is None
    conn = conn or connection()
    try:
        for table, key in [("orders", "order_id"), ("physical_items", "item_id"),
                           ("products", "product_id"), ("customizations", "customization_id")]:
            bad = conn.execute(f"SELECT {key} FROM {table} GROUP BY {key} HAVING {key} IS NULL OR COUNT(*) != 1").fetchall()
            if bad:
                raise GrainError(f"{table} violates its declared non-null unique key.")
        if conn.execute("SELECT COUNT(*) FROM physical_items WHERE typeof(sale_cents) != 'integer' OR sale_cents < 0").fetchone()[0]:
            raise GrainError("Sales must be nonnegative integer cents.")
        for query in [
            "SELECT COUNT(*) FROM physical_items i LEFT JOIN orders o USING(order_id) WHERE o.order_id IS NULL",
            "SELECT COUNT(*) FROM customizations d LEFT JOIN physical_items i USING(item_id) WHERE i.item_id IS NULL",
        ]:
            if conn.execute(query).fetchone()[0]:
                raise GrainError("A physical item or customization has no declared parent.")
        source = conn.execute("SELECT item_id, order_id, sale_cents FROM physical_items ORDER BY item_id").fetchall()
        safe = conn.execute((FIXTURES / "grain_safe.sql").read_text(encoding="utf-8") + " ORDER BY i.item_id").fetchall()
        if [row[:3] for row in safe] != source:
            raise GrainError("The proposed join changed the item-grain financial contract.")
        naive = conn.execute("SELECT COUNT(*), SUM(i.sale_cents) FROM physical_items i LEFT JOIN customizations d USING(item_id)").fetchone()
        dropped = conn.execute("SELECT SUM(i.sale_cents) FROM physical_items i INNER JOIN products p USING(product_id)").fetchone()[0]
        return {
            "data_origin": "invented retail records; integer cents",
            "contract": "one physical item per item_id; customization records do not create sales",
            "correct": {"orders": len({row[1] for row in safe}), "physical_units": len(safe),
                        "revenue_cents": sum(row[2] for row in safe),
                        "customization_records": sum(row[4] for row in safe),
                        "unmapped_product_units": sum(row[3] == "Unmapped" for row in safe)},
            "naive_customization_join": {"rows": naive[0], "revenue_cents": naive[1]},
            "inner_product_join": {"revenue_cents": dropped},
            "items": [dict(zip(("item_id", "order_id", "sale_cents", "category", "customization_count"), row)) for row in safe],
            "limits": "No proprietary customization pricing or manufacturing rules; no cloud execution.",
        }
    finally:
        if own:
            conn.close()
