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


def test_finance_model_sql_and_all_four_singular_tests():
    conn=connection();build_finance(conn)
    assert conn.execute("SELECT SUM(total_revenue) FROM mart_revenue_by_segment").fetchone()[0]==450
    assert conn.execute("SELECT SUM(total_gross_margin) FROM mart_revenue_by_segment").fetchone()[0]==310
    for name in ('finance_revenue_grain','finance_category_grain','finance_revenue_reconciliation','finance_category_reconciliation'):
        assert conn.execute(render(f"tests/{name}.sql")).fetchall()==[]
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
