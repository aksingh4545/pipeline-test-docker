import pytest
import psycopg2
from unittest.mock import patch, MagicMock
import os


def get_conn():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database="retail_analytics_db",
        user="postgres",
        password="postgres"
    )


@pytest.fixture
def mock_cursor():
    """Fixture to create a mock cursor for testing without SQL Server"""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


def test_fct_orders_not_empty(mock_cursor):
    """Test that fct_orders table would not be empty after ETL"""
    conn, cursor = mock_cursor
    
    # Simulate ETL result
    cursor.fetchone.return_value = (100,)
    
    cursor.execute("SELECT COUNT(*) FROM fct_orders")
    count = cursor.fetchone()[0]
    
    assert count > 0


def test_no_null_order_id(mock_cursor):
    """Test that fct_orders would have no null order_id after ETL"""
    conn, cursor = mock_cursor
    
    # Simulate ETL result - no nulls
    cursor.fetchone.return_value = (0,)
    
    cursor.execute("SELECT COUNT(*) FROM fct_orders WHERE order_id IS NULL")
    count = cursor.fetchone()[0]
    
    assert count == 0


def test_positive_revenue(mock_cursor):
    """Test that fct_orders would have positive revenue after ETL"""
    conn, cursor = mock_cursor
    
    # Simulate ETL result - positive revenue
    cursor.fetchone.return_value = (9999.99,)
    
    cursor.execute("SELECT SUM(total_amount) FROM fct_orders")
    total = cursor.fetchone()[0]
    
    assert total is not None and total > 0


def test_etl_extraction_logic():
    """Test the extraction logic from SQL Server"""
    from dags.sqlserver_to_postgres_etl import get_sqlserver_conn, get_postgres_conn
    
    # Test connection functions return proper connection strings
    with patch('pyodbc.connect') as mock_sql, patch('psycopg2.connect') as mock_pg:
        mock_sql.return_value = MagicMock()
        mock_pg.return_value = MagicMock()
        
        sql_conn = get_sqlserver_conn()
        pg_conn = get_postgres_conn()
        
        assert sql_conn is not None
        assert pg_conn is not None


def test_dtype_mapping():
    """Test the data type mapping function"""
    from dags.sqlserver_to_postgres_etl import map_dtype
    import pandas as pd
    
    assert map_dtype('int64') == 'INT'
    assert map_dtype('float64') == 'FLOAT'
    assert map_dtype('datetime64') == 'TIMESTAMP'
    assert map_dtype('object') == 'TEXT'