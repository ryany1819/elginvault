from db.connection import get_db_connection
from db.queries import (
    load_sql_query,
    execute_nonquery,
    fetch_query_results,
    fetch_query_single_result,
)
from app.repositories.exceptions import RepositoryException


def insert_vault_catalog(conn, ticker, start_time, end_time):
    sql = load_sql_query('db/queries/insert_stock_vault_entry.sql')
    if not sql:
        raise RepositoryException('SQL query not found.')
    try:
        execute_nonquery(conn, sql, (ticker, start_time, end_time))
    except Exception as e:
        print(e)
        raise RepositoryException(f'Error executing insert: {e}')


def get_vault_catalog_by_ticker(conn, ticker):
    sql = load_sql_query('db/queries/get_stock_vault_entry_by_ticker.sql')
    if not sql:
        raise RepositoryException('SQL query not found.')
    try:
        print(sql, ticker)
        result = fetch_query_single_result(conn, sql, (ticker,))
        return result if result else None
    except Exception as e:
        print(e)
        raise RepositoryException(f'Error executing query: {e}')


def get_vault_catalog_list(conn):
    sql = load_sql_query('db/queries/get_all_stock_vault_catalog.sql')
    if not sql:
        raise RepositoryException('SQL query not found.')
    try:
        results = fetch_query_results(conn, sql)
        return results if results else []
    except Exception as e:
        print(e)
        raise RepositoryException('Error executing query: {e}')


def delete_vault_catalog_by_ticker(conn, ticker):
    sql = load_sql_query('db/queries/delete_stock_vault_entry_by_ticker.sql')
    if not sql:
        raise RepositoryException('SQL query not found.')
    try:
        execute_nonquery(conn, sql, (ticker,))
    except Exception as e:
        print(e)
        raise RepositoryException(f'Error executing query: {e}')
