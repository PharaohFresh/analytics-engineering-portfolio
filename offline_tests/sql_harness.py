from pathlib import Path
import sqlite3

from jinja2 import Environment, StrictUndefined
import sqlglot
from sqlglot import exp


ROOT = Path(__file__).resolve().parents[1]


def sqlite_sql(sql):
    expression = sqlglot.parse_one(sql, read="bigquery")
    for table in expression.find_all(exp.Table):
        table.set("db", None)
        table.set("catalog", None)
    return expression.sql(dialect="sqlite")


def render(relative_path, incremental=False):
    template = Environment(undefined=StrictUndefined).from_string((ROOT / relative_path).read_text(encoding="utf-8"))
    return sqlite_sql(template.render(config=lambda **kwargs: "", ref=lambda name: name,
                                     is_incremental=lambda: incremental, this="fct_order_items"))


def connection():
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
      CREATE TABLE stg_order_items (order_item_key INTEGER, order_key INTEGER, customer_key INTEGER,
        product_key INTEGER, item_status TEXT, sale_price REAL, item_created_at TEXT, order_date TEXT,
        shipped_at TEXT, delivered_at TEXT, returned_at TEXT);
      CREATE TABLE stg_orders (order_key INTEGER, customer_key INTEGER, order_status TEXT);
      CREATE TABLE stg_products (product_key INTEGER, product_name TEXT, brand TEXT, category TEXT,
        department TEXT, cost REAL, retail_price REAL, distribution_center_key INTEGER);
      CREATE TABLE stg_distribution_centers (distribution_center_key INTEGER, distribution_center_name TEXT);
      CREATE TABLE dim_customers (customer_key INTEGER, traffic_source TEXT, country TEXT);
      INSERT INTO stg_orders VALUES (101,1,'Complete'), (102,2,'Complete'), (103,1,'Complete');
      INSERT INTO stg_products VALUES (1,'Cup','Invented','Drinkware','Home',30,100,1),
        (2,'Bag','Invented','Bags','Gear',50,200,1), (3,'Cap','Invented','Headwear','Gear',60,150,1);
      INSERT INTO stg_distribution_centers VALUES (1,'Synthetic center');
      INSERT INTO dim_customers VALUES (1,'Search','US'), (2,'Email','CA');
      INSERT INTO stg_order_items VALUES
        (1,101,1,1,'Complete',100,'2026-09-01T10:00:00','2026-09-01',NULL,NULL,NULL),
        (2,102,2,2,'Complete',200,'2026-09-02T10:00:00','2026-09-02',NULL,NULL,NULL),
        (3,103,1,3,'Complete',150,'2026-09-03T10:00:00','2026-09-03',NULL,NULL,NULL);
      CREATE TABLE fct_orders AS SELECT order_key, customer_key FROM stg_orders;
    """)
    apply_fact(conn, full_refresh=True)
    return conn


def apply_fact(conn, full_refresh=False):
    conn.execute("DROP TABLE IF EXISTS int_order_items_enriched")
    conn.execute("CREATE TEMP TABLE int_order_items_enriched AS " + render("models/intermediate/int_order_items_enriched.sql"))
    if full_refresh:
        conn.execute("DROP TABLE IF EXISTS fct_order_items")
        conn.execute("CREATE TABLE fct_order_items AS " + render("models/marts/core/fct_order_items.sql"))
    else:
        # Exercise actual incremental SELECT, then simulate keyed replacement.
        # This is not a test of BigQuery's MERGE engine or dbt's generated DML.
        conn.execute("CREATE TEMP TABLE candidate AS " + render("models/marts/core/fct_order_items.sql", incremental=True))
        conn.execute("DELETE FROM fct_order_items WHERE order_item_key IN (SELECT order_item_key FROM candidate)")
        conn.execute("INSERT INTO fct_order_items SELECT * FROM candidate")
        conn.execute("DROP TABLE candidate")


def build_finance(conn):
    for name in ("mart_revenue_by_segment", "mart_product_category_margin"):
        conn.execute(f"DROP TABLE IF EXISTS {name}")
        conn.execute(f"CREATE TABLE {name} AS " + render(f"models/marts/finance/{name}.sql"))
