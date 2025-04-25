import pytest
from datetime import datetime

from app.repositories.stock_data_repository import (
    insert_vault_data_bulk,
    get_vault_data_by_ticker_and_time_range,
)
from app.repositories.stock_vault_catalog_repository import insert_stock_vault_catalog
from app.repositories.exceptions import RepositoryException
from app.models import StockData


def test_bulk_insert_stock_data(mocker):
    # Mock database connection and query execution
    mock_conn = mocker.patch('app.repositories.stock_data_repository.get_db_connection')
    mock_execute_nonquery = mocker.patch(
        'app.repositories.stock_data_repository.execute_nonquery'
    )

    # Mock the database connection context manager
    mock_conn.return_value.__enter__.return_value = 'mock_connection'

    # Mock the SQL query loading
    mock_load_sql_query = mocker.patch(
        'app.repositories.stock_data_repository.load_sql_query',
        return_value='INSERT INTO stock_data ...',
    )

    # Test with valid records
    records = [
        StockData(
            timestamp=datetime.strptime('2023-01-01', '%Y-%m-%d'),
            ticker='AAPL',
            open=150.0,
            high=155.0,
            low=149.0,
            close=154.0,
            volume=1000,
        )
    ]
    insert_vault_data_bulk(records)
    mock_execute_nonquery.assert_called_once_with(
        'mock_connection',
        'INSERT INTO stock_data ...',
        [
            (
                record.timestamp,
                record.ticker,
                record.open,
                record.high,
                record.low,
                record.close,
                record.volume,
            )
            for record in records
        ],
        bulk=True,
    )

    # Test with SQL query not found
    mock_load_sql_query.return_value = None
    with pytest.raises(RepositoryException, match='SQL query not found.'):
        insert_vault_data_bulk(records)

    # Test with database execution error
    mock_load_sql_query.return_value = 'INSERT INTO stock_data ...'
    mock_execute_nonquery.side_effect = Exception('Database error')
    with pytest.raises(
        RepositoryException, match='Error executing bulk insert: Database error'
    ):
        insert_vault_data_bulk(records)

    # Test with missing records
    missing_records = None
    with pytest.raises(RepositoryException, match='No records to insert.'):
        insert_vault_data_bulk(missing_records)

    # Test with invalid SQL query
    mock_load_sql_query.return_value = 'INVALID SQL QUERY'
    with pytest.raises(RepositoryException, match='Error executing bulk insert:'):
        insert_vault_data_bulk(records)


def test_get_stock_data_by_ticker_and_time_range(mocker):
    # Mock database connection and query execution
    mock_conn = mocker.patch('app.repositories.stock_data_repository.get_db_connection')
    mock_fetch_query_results = mocker.patch(
        'app.repositories.stock_data_repository.fetch_query_results'
    )

    # Mock the database connection context manager
    mock_conn.return_value.__enter__.return_value = 'mock_connection'

    # Mock the SQL query loading
    mock_load_sql_query = mocker.patch(
        'app.repositories.stock_data_repository.load_sql_query',
        return_value='SELECT * FROM stock_data WHERE ticker = %s AND time >= %s AND time <= %s',
    )

    # Test with valid parameters
    ticker = 'AAPL'
    start_time = '2023-01-01'
    end_time = '2023-01-31'
    get_vault_data_by_ticker_and_time_range(ticker, start_time, end_time)
    mock_fetch_query_results.assert_called_once_with(
        'mock_connection',
        'SELECT * FROM stock_data WHERE ticker = %s AND time >= %s AND time <= %s',
        (ticker, start_time, end_time),
    )

    # Test with SQL query not found
    mock_load_sql_query.return_value = None
    with pytest.raises(RepositoryException, match='SQL query not found.'):
        get_vault_data_by_ticker_and_time_range(ticker, start_time, end_time)

    # Test with database execution error
    mock_load_sql_query.return_value = (
        'SELECT * FROM stock_data WHERE ticker = %s AND time >= %s AND time <= %s'
    )
    mock_fetch_query_results.side_effect = Exception('Database error')
    with pytest.raises(
        RepositoryException, match='Error executing query: Database error'
    ):
        get_vault_data_by_ticker_and_time_range(ticker, start_time, end_time)


def test_create_stock_vault_catalog_entry(mocker):
    mock_conn = mocker.patch(
        'app.repositories.stock_vault_catalog_repository.get_db_connection'
    )
    mock_execute_nonquery = mocker.patch(
        'app.repositories.stock_vault_catalog_repository.execute_nonquery'
    )
    mock_conn.return_value.__enter__.return_value = 'mock_connection'

    # Test with valid parameters
    insert_stock_vault_catalog(
        ticker='AAPL',
        start_time='2023-01-01T00:00:00Z',
        end_time='2024-01-31T23:59:59Z',
    )
    mock_execute_nonquery.assert_called_once()
