from datetime import datetime

from db.connection import get_db_connection
from db.queries import (
    load_sql_query,
    execute_nonquery,
    fetch_query_results,
)
from app.repositories.exceptions import RepositoryException
from app.models import StockData


def insert_vault_data_bulk(conn, records: list[StockData]):
    '''
    Inserts stock data records into the database in bulk.
    '''
    sql = load_sql_query('db/queries/insert_stock_data.sql')
    if not sql:
        raise RepositoryException('SQL query not found.')
    if not records:
        raise RepositoryException('No records to insert.')
    try:
        execute_nonquery(
            conn,
            sql,
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
    except Exception as e:
        print(e)
        raise RepositoryException(f'Error executing bulk insert: {e}')


def get_vault_data_by_ticker_and_time_range(
    conn, ticker: str, start_time: str, end_time: str
):
    '''
    Retrieves stock data for a given ticker symbol within a specified time range.
    '''
    sql = load_sql_query('db/queries/get_stock_data_by_ticker_and_time_range.sql')
    if not sql:
        raise RepositoryException('SQL query not found.')
    try:
        results = fetch_query_results(conn, sql, (ticker, start_time, end_time))
        return results if results else []
    except Exception as e:
        print(e)
        raise RepositoryException(f'Error executing query: {e}')


def delete_vault_data_by_ticker(conn, ticker: str):
    sql = load_sql_query('db/queries/delete_stock_data_by_ticker.sql')
    if not sql:
        raise RepositoryException('SQL query not found.')
    try:
        execute_nonquery(conn, sql, (ticker,))
    except Exception as e:
        print(e)
        raise RepositoryException(f'Error executing query: {e}')
