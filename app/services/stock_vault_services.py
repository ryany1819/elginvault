import logging

from app.models import StockData, StockCatalog
from app.repositories.stock_data_repository import (
    delete_vault_data_by_ticker,
    insert_vault_data_bulk,
    get_vault_data_by_ticker_and_time_range,
)
from app.repositories.stock_vault_catalog_repository import (
    delete_vault_catalog_by_ticker,
    insert_vault_catalog,
    get_vault_catalog_list,
    get_vault_catalog_by_ticker,
)
from db.connection import get_db_connection


def import_stock_vault(
    ticker: str, start_time: str, end_time: str, records: list[StockData]
):
    with get_db_connection() as conn:
        try:
            insert_vault_data_bulk(conn, records)
            insert_vault_catalog(
                conn,
                ticker=ticker,
                start_time=start_time,
                end_time=end_time,
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f'Error adding stock vault: {e}')
            raise e


def remove_stock_vault(ticker: str):
    with get_db_connection() as conn:
        try:
            if not ticker:
                raise ValueError('ticker symbol is required.')
            delete_vault_data_by_ticker(conn, ticker)
            delete_vault_catalog_by_ticker(conn, ticker)
            conn.commit()
            return {
                'ticker': ticker,
                'message': f'Stock vault for {ticker} deleted successfully.',
            }
        except Exception as e:
            conn.rollback()
            logging.error(f'Error deleting stock data: {e}')
            raise e


def fetch_stock_vault_catalog_list():
    with get_db_connection() as conn:
        try:
            for record in get_vault_catalog_list(conn):
                yield StockCatalog(**{
                    'ticker': record[0],
                    'start_time': record[1],
                    'end_time': record[2],
                    'inserted_at': record[3],
                })
        except Exception as e:
            logging.error(f'Error retrieving stock vault catalog list: {e}')
            raise e


def query_stock_vault_catalog_ticker(ticker: str):
    with get_db_connection() as conn:
        try:
            record = get_vault_catalog_by_ticker(conn, ticker)
            return StockCatalog(**{
                    'ticker': record[0],
                    'start_time': record[1],
                    'end_time': record[2],
                    'inserted_at': record[3],
                }) if record else None
        except Exception as e:
            logging.error(f'Error retrieveing stock vault catalog: {e}')
            raise e


def query_stock_vault_data(ticker: str, start_time: str, end_time: str):
    with get_db_connection() as conn:
        try:
            for record in get_vault_data_by_ticker_and_time_range(
                conn,
                ticker=ticker,
                start_time=start_time,
                end_time=end_time,
            ):
                yield StockData(**{
                    'timestamp': record[0],
                    'ticker': record[1],
                    'open': record[2],
                    'high': record[3],
                    'low': record[4],
                    'close': record[5],
                    'volume': record[6],
                })
        except Exception as e:
            logging.error(f'Error retrieving stock data: {e}')
            raise e
