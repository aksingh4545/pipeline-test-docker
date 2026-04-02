import psycopg2


def get_conn():
    return psycopg2.connect(
        host="localhost",
        database="retail_analytics_db",
        user="postgres",
        password="postgres"
    )


def test_fct_orders_not_empty():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM fct_orders")
    count = cursor.fetchone()[0]

    assert count > 0

    cursor.close()
    conn.close()


def test_no_null_order_id():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM fct_orders WHERE order_id IS NULL")
    count = cursor.fetchone()[0]

    assert count == 0

    cursor.close()
    conn.close()


def test_positive_revenue():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(total_amount) FROM fct_orders")
    total = cursor.fetchone()[0]

    assert total is not None and total > 0

    cursor.close()
    conn.close()