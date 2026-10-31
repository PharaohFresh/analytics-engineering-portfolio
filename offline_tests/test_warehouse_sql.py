import pytest

from scripts.qa_contracts import queries
from .sql_harness import apply_fact, build_finance, connection, render, sqlite_sql


def failed_checks(conn):
    return [label for label, sql in queries("synthetic-project", "synthetic_dataset") if conn.execute(sqlite_sql(sql)).fetchone()[0] != 0]


def test_old_item_updates_and_current_product_enrichment_are_not_skipped():
    conn=connection()
    conn.execute("UPDATE stg_order_items SET item_status='Returned', returned_at='2026-09-05T10:00:00' WHERE order_item_key=1")
    conn.execute("UPDATE stg_products SET cost=35, category='Cups' WHERE product_key=1")
    apply_fact(conn)
    assert conn.execute("SELECT item_status, is_returned, unit_cost, gross_margin, category FROM fct_order_items WHERE order_item_key=1").fetchone()==('Returned',1,35,65,'Cups')
    assert failed_checks(conn)==[]


@pytest.mark.parametrize("created_at", ["2026-09-03T10:00:00", "2026-08-01T10:00:00"])
def test_timestamp_ties_and_late_arrivals_are_included(created_at):
    conn=connection()
    conn.execute("INSERT INTO stg_order_items SELECT 4, order_key, customer_key, product_key, item_status, sale_price, ?, order_date, shipped_at, delivered_at, returned_at FROM stg_order_items WHERE order_item_key=1",(created_at,))
    apply_fact(conn)
    assert conn.execute("SELECT COUNT(*) FROM fct_order_items").fetchone()[0]==4
    assert failed_checks(conn)==[]


def test_repeated_merge_is_idempotent_and_deletions_require_full_refresh():
    conn=connection();apply_fact(conn);before=conn.execute("SELECT * FROM fct_order_items ORDER BY order_item_key").fetchall()
    apply_fact(conn)
    assert conn.execute("SELECT * FROM fct_order_items ORDER BY order_item_key").fetchall()==before
    conn.execute("DELETE FROM stg_order_items WHERE order_item_key=1");apply_fact(conn)
    assert 'item key sets match source' in failed_checks(conn)
    apply_fact(conn,full_refresh=True)
    assert failed_checks(conn)==[]


@pytest.mark.parametrize("mutation,expected", [
 ("UPDATE fct_order_items SET sale_price=sale_price+1 WHERE order_item_key=1", "values and parent"),
 ("UPDATE fct_order_items SET sale_price=CASE order_item_key WHEN 1 THEN 101 WHEN 2 THEN 199 ELSE sale_price END", "values and parent"),
 ("UPDATE fct_order_items SET order_key=102 WHERE order_item_key=1", "values and parent"),
 ("UPDATE fct_order_items SET returned_at='2026-09-05',is_returned=1 WHERE order_item_key=1", "values and parent"),
 ("UPDATE fct_order_items SET order_item_key=1 WHERE order_item_key=2", "keys are unique"),
 ("UPDATE fct_order_items SET order_item_key=NULL WHERE order_item_key=1", "keys are non-null"),
 ("UPDATE fct_orders SET order_key=101 WHERE order_key=102", "order keys are unique"),
 ("UPDATE fct_orders SET order_key=NULL WHERE order_key=101", "order keys are non-null"),
])
def test_independent_audit_detects_same_count_corruption(mutation,expected):
    conn=connection();conn.execute(mutation)
    assert any(expected in label for label in failed_checks(conn))


def test_order_fact_runs_the_real_model_and_keeps_itemless_orders():
    conn = connection()
    rows = conn.execute("SELECT order_key, customer_key, order_date, order_status, num_items, delivered_at, item_count, "
                        "total_revenue, total_gross_margin, returned_item_count FROM fct_orders ORDER BY order_key").fetchall()
    assert rows == [
        (101, 1, '2026-09-01', 'Complete', 1, None, 1, 100, 70, 0),
        (102, 2, '2026-09-02', 'Complete', 1, '2026-09-05T10:00:00', 1, 200, 150, 0),
        (103, 1, '2026-09-03', 'Complete', 1, None, 1, 150, 90, 0),
        (104, 2, '2026-09-04', 'Cancelled', 0, None, None, None, None, None),
    ]
    assert failed_checks(conn) == []


@pytest.mark.parametrize("mutation", [
    "UPDATE fct_orders SET customer_key=2 WHERE order_key=101",
    "UPDATE fct_orders SET order_date='2026-08-31' WHERE order_key=101",
    "UPDATE fct_orders SET order_status='Returned' WHERE order_key=101",
    "UPDATE fct_orders SET num_items=2 WHERE order_key=101",
    "UPDATE fct_orders SET delivered_at=NULL WHERE order_key=102",
    "UPDATE fct_orders SET item_count=2 WHERE order_key=101",
    "UPDATE fct_orders SET total_revenue=total_revenue+50 WHERE order_key=101",
    "UPDATE fct_orders SET total_gross_margin=total_gross_margin+1 WHERE order_key=101",
    # An itemless order has no rollup; only the null-mismatch predicate catches a zero total.
    "UPDATE fct_orders SET total_revenue=0 WHERE order_key=104",
])
def test_order_values_and_rollups_are_checked_by_key(mutation):
    # Before the keyed order check, these same-count changes passed every QA contract.
    conn = connection()
    conn.execute(mutation)
    assert failed_checks(conn) == ['order values match source and rollups match the item fact by key']


SINGULAR_FINANCE_TESTS = (
    'finance_revenue_grain', 'finance_category_grain',
    'finance_revenue_reconciliation', 'finance_category_reconciliation',
    'finance_revenue_bucket_reconciliation', 'finance_category_bucket_reconciliation',
)
BUCKET_TESTS = {'finance_revenue_bucket_reconciliation', 'finance_category_bucket_reconciliation'}


def finance_failures(conn):
    return [name for name in SINGULAR_FINANCE_TESTS if conn.execute(render(f"tests/{name}.sql")).fetchall()]


def test_finance_marts_produce_exact_expected_rows():
    conn = connection()
    build_finance(conn)
    assert conn.execute("SELECT * FROM mart_revenue_by_segment ORDER BY traffic_source, country").fetchall() == [
        ('Email', 'CA', 1, 1, 200, 150, 200.0),
        ('Search', 'US', 2, 2, 250, 160, 125.0),
    ]
    assert conn.execute("SELECT * FROM mart_product_category_margin ORDER BY department, category").fetchall() == [
        ('Gear', 'Bags', 1, 200, 150, 0.75, 0, 0.0),
        ('Gear', 'Headwear', 1, 150, 90, 0.6, 0, 0.0),
        ('Home', 'Drinkware', 1, 100, 70, 0.7, 0, 0.0),
    ]


@pytest.mark.parametrize("mutation", [
    "UPDATE mart_revenue_by_segment SET country=CASE country WHEN 'US' THEN 'CA' ELSE 'US' END",
    "UPDATE mart_product_category_margin SET total_revenue=total_revenue+CASE category WHEN 'Bags' THEN 50 WHEN 'Headwear' THEN -50 ELSE 0 END",
    "UPDATE mart_revenue_by_segment SET order_count=order_count+7, avg_order_value=1 WHERE country='US'",
    "UPDATE mart_revenue_by_segment SET avg_order_value=avg_order_value+1 WHERE country='US'",
    "UPDATE mart_revenue_by_segment SET units_sold=units_sold+1 WHERE country='CA'",
    "UPDATE mart_product_category_margin SET return_rate=0.9 WHERE category='Bags'",
    "UPDATE mart_product_category_margin SET gross_margin_pct=0.01 WHERE category='Bags'",
    "DELETE FROM mart_product_category_margin WHERE category='Bags'",
    "INSERT INTO mart_revenue_by_segment VALUES ('Display','MX',1,1,0,0,0)",
])
def test_bucket_level_finance_corruption_fails_a_keyed_check(mutation):
    # Several of these keep every total intact, so only the keyed bucket checks can see them.
    conn = connection()
    build_finance(conn)
    assert finance_failures(conn) == []
    conn.execute(mutation)
    assert BUCKET_TESTS & set(finance_failures(conn))


def test_finance_model_sql_and_all_six_singular_tests():
    conn=connection();build_finance(conn)
    assert conn.execute("SELECT SUM(total_revenue) FROM mart_revenue_by_segment").fetchone()[0]==450
    assert conn.execute("SELECT SUM(total_gross_margin) FROM mart_revenue_by_segment").fetchone()[0]==310
    assert finance_failures(conn)==[]
    conn.execute("INSERT INTO mart_revenue_by_segment SELECT * FROM mart_revenue_by_segment WHERE country='US'")
    assert conn.execute(render("tests/finance_revenue_grain.sql")).fetchall()
    assert conn.execute(render("tests/finance_revenue_reconciliation.sql")).fetchall()
    conn.execute("UPDATE mart_product_category_margin SET units_returned=1 WHERE category='Bags'")
    assert conn.execute(render("tests/finance_category_reconciliation.sql")).fetchall()


def test_financial_tolerance_is_explicit_and_does_not_accept_material_drift():
    conn=connection();build_finance(conn)
    conn.execute("UPDATE mart_revenue_by_segment SET total_revenue=total_revenue+0.0000001 WHERE country='US'")
    assert conn.execute(render("tests/finance_revenue_reconciliation.sql")).fetchall()==[]
    conn.execute("UPDATE mart_revenue_by_segment SET total_revenue=total_revenue+1 WHERE country='US'")
    assert conn.execute(render("tests/finance_revenue_reconciliation.sql")).fetchall()


def test_category_margin_corruption_is_detected():
    conn=connection();build_finance(conn)
    conn.execute('UPDATE mart_product_category_margin SET total_gross_margin=total_gross_margin+999')
    assert conn.execute(render('tests/finance_category_reconciliation.sql')).fetchall()
