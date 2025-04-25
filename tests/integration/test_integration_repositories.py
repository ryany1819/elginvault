import pytest
from datetime import datetime
from db.connection import get_db_connection, close_db_connection
from db.queries import load_sql_query, fetch_query_single_result, fetch_query_results
from app.repositories.stock_data_repository import (
    insert_vault_data_bulk,
    get_vault_data_by_ticker_and_time_range,
)
from app.repositories.stock_vault_catalog_repository import (
    insert_stock_vault_catalog,
    get_vault_catalog_by_ticker,
    get_vault_catalog_list,
)
from app.models import StockData


@pytest.fixture(scope='module', autouse=True)
def setup_module():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                '''
                DELETE FROM stock_vault_catalog;
                DELETE FROM stock_data;
                '''
            )
            conn.commit()
    yield
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                '''
                DELETE FROM stock_vault_catalog;
                DELETE FROM stock_data;
                '''
            )
            conn.commit()


@pytest.mark.integration
def test_create_stock_vault_catalog_entry():
    insert_stock_vault_catalog(
        ticker='AAPL',
        start_time='2023-01-01',
        end_time='2023-01-02',
    )
    with get_db_connection() as conn:
        sql = load_sql_query('db/queries/get_stock_vault_entry_by_ticker.sql')
        result = fetch_query_single_result(conn, sql, ('AAPL',))
        assert result is not None, 'Failed to create stock vault catalog entry'
        assert result[0] == 'AAPL', 'Ticker mismatch'


@pytest.mark.integration
def test_insert_stock_data_bulk():
    records = [
        StockData(
            timestamp=datetime.strptime('2023-01-01', '%Y-%m-%d'),
            ticker='AAPL',
            open=150.0,
            high=155.0,
            low=145.0,
            close=152.0,
            volume=100000,
        ),
        StockData(
            timestamp=datetime.strptime('2023-01-02', '%Y-%m-%d'),
            ticker='AAPL',
            open=152.0,
            high=158.0,
            low=148.0,
            close=156.0,
            volume=120000,
        ),
    ]
    insert_vault_data_bulk(records)
    with get_db_connection() as conn:
        sql = load_sql_query('db/queries/get_stock_data_by_ticker_and_time_range.sql')
        results = fetch_query_results(
            conn,
            sql,
            ('AAPL', '2023-01-01', '2023-01-02'),
        )
        assert results is not None, 'Failed to insert stock data'
        assert len(results) == 2, 'Inserted records count mismatch'
        assert results[0][1] == 'AAPL', 'Ticker mismatch'


@pytest.mark.integration
def test_get_stock_data_by_ticker_and_time_range():
    results = get_vault_data_by_ticker_and_time_range(
        ticker='AAPL',
        start_time='2023-01-01',
        end_time='2023-01-02',
    )
    assert results is not None, 'Failed to retrieve stock data'
    assert len(results) == 2, 'Retrieved records count mismatch'
    assert results[0][1] == 'AAPL', 'Ticker mismatch'
