from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import pyodbc
import psycopg2
from psycopg2.extras import execute_batch


# ---------------------------
# CONNECTIONS
# ---------------------------

def get_sqlserver_conn():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=sqlserver,1433;"
        "DATABASE=retail_ops_db;"
        "UID=sa;"
        "PWD=ankit4539047@"
    )

def get_postgres_conn():
    return psycopg2.connect(
        host="postgres",
        database="retail_analytics_db",
        user="postgres",
        password="postgres"
    )


# ---------------------------
# EXTRACT + STAGING (FIXED)
# ---------------------------

def map_dtype(dtype):
    if "int" in str(dtype):
        return "INT"
    elif "float" in str(dtype):
        return "FLOAT"
    elif "datetime" in str(dtype):
        return "TIMESTAMP"
    else:
        return "TEXT"


def extract_and_stage(table_name):
    sql_conn = get_sqlserver_conn()
    pg_conn = get_postgres_conn()
    cursor = pg_conn.cursor()

    df = pd.read_sql(f"SELECT * FROM {table_name}", sql_conn)

    if df.empty:
        print(f"No data in {table_name}")
        return

    # Drop + recreate staging table
    cursor.execute(f"DROP TABLE IF EXISTS stg_{table_name}")

    columns = [
        f"{col} {map_dtype(dtype)}"
        for col, dtype in zip(df.columns, df.dtypes)
    ]

    cursor.execute(f"""
        CREATE TABLE stg_{table_name} (
            {', '.join(columns)}
        )
    """)

    # Batch insert (FAST)
    placeholders = ','.join(['%s'] * len(df.columns))
    insert_query = f"INSERT INTO stg_{table_name} VALUES ({placeholders})"
    
    # FINAL FIX
    df = df.astype(object).where(pd.notnull(df), None)
    
    data = [tuple(row) for row in df.to_numpy()]
    execute_batch(cursor, insert_query, data)


    pg_conn.commit()

    cursor.close()
    sql_conn.close()
    pg_conn.close()


# ---------------------------
# INTERMEDIATE (FIXED)
# ---------------------------

def build_intermediate():
    conn = get_postgres_conn()
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS int_orders_enriched")

    cursor.execute("""
    CREATE TABLE int_orders_enriched AS
    SELECT
        o.order_id,
        o.customer_id,
        c.first_name,
        c.last_name,
        o.order_date,
        p.payment_method,
        s.status AS shipment_status
    FROM stg_orders o
    LEFT JOIN stg_customers c ON o.customer_id = c.customer_id
    LEFT JOIN stg_payments p ON o.order_id = p.order_id
    LEFT JOIN stg_shipments s ON o.order_id = s.order_id;
    """)

    conn.commit()
    cursor.close()
    conn.close()


# ---------------------------
# MARTS (FIXED)
# ---------------------------

def build_marts():
    conn = get_postgres_conn()
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS fct_orders")
    cursor.execute("""
    CREATE TABLE fct_orders AS
    SELECT
        o.order_id,
        o.customer_id,
        o.order_date,
        SUM(p.amount) AS total_amount
    FROM stg_orders o
    JOIN stg_payments p ON o.order_id = p.order_id
    GROUP BY o.order_id, o.customer_id, o.order_date;
    """)

    cursor.execute("DROP TABLE IF EXISTS dim_customers")
    cursor.execute("""
    CREATE TABLE dim_customers AS
    SELECT DISTINCT customer_id, first_name, last_name, email
    FROM stg_customers;
    """)

    cursor.execute("DROP TABLE IF EXISTS dim_products")
    cursor.execute("""
    CREATE TABLE dim_products AS
    SELECT DISTINCT product_id, product_name, category
    FROM stg_products;
    """)

    conn.commit()
    cursor.close()
    conn.close()


# ---------------------------
# AGGREGATIONS (FIXED)
# ---------------------------

def build_aggregations():
    conn = get_postgres_conn()
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS agg_daily_sales")
    cursor.execute("""
    CREATE TABLE agg_daily_sales AS
    SELECT
        DATE(order_date) AS sales_date,
        SUM(total_amount) AS daily_revenue
    FROM fct_orders
    GROUP BY DATE(order_date);
    """)

    cursor.execute("DROP TABLE IF EXISTS agg_customer_metrics")
    cursor.execute("""
    CREATE TABLE agg_customer_metrics AS
    SELECT
        customer_id,
        COUNT(order_id) AS total_orders,
        SUM(total_amount) AS lifetime_value
    FROM fct_orders
    GROUP BY customer_id;
    """)

    conn.commit()
    cursor.close()
    conn.close()




def validate_data():
    conn = get_postgres_conn()
    cursor = conn.cursor()

    # 1. Check data exists
    cursor.execute("SELECT COUNT(*) FROM fct_orders")
    fct_count = cursor.fetchone()[0]

    if fct_count == 0:
        raise ValueError("❌ fct_orders is empty")

    # 2. Check NULLs in critical fields
    cursor.execute("""
        SELECT COUNT(*) FROM fct_orders
        WHERE order_id IS NULL OR customer_id IS NULL
    """)
    null_count = cursor.fetchone()[0]

    if null_count > 0:
        raise ValueError(f"❌ Found {null_count} NULL records in fct_orders")

    # 3. Check aggregation sanity
    cursor.execute("SELECT SUM(total_amount) FROM fct_orders")
    total = cursor.fetchone()[0]

    if total is None or total <= 0:
        raise ValueError("❌ Invalid total revenue")

    print(f"✅ Validation passed | rows={fct_count}, revenue={total}")

    cursor.close()
    conn.close()


# ---------------------------
# DAG
# ---------------------------

with DAG(
    dag_id='full_etl_pipeline',
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False
) as dag:

    tables = [
        "customers",
        "products",
        "orders",
        "order_items",
        "payments",
        "shipments"
    ]

    extract_tasks = [
        PythonOperator(
            task_id=f"extract_{table}",
            python_callable=extract_and_stage,
            op_args=[table]
        )
        for table in tables
    ]

    transform_task = PythonOperator(
        task_id="build_intermediate",
        python_callable=build_intermediate
    )

    mart_task = PythonOperator(
        task_id="build_marts",
        python_callable=build_marts
    )

    agg_task = PythonOperator(
        task_id="build_aggregations",
        python_callable=build_aggregations
    )

    validation_task = PythonOperator(
    task_id="validate_data",
    python_callable=validate_data
)

    extract_tasks >> transform_task >> mart_task >> agg_task >> validation_task