import psycopg2
from psycopg2.extras import execute_values  # Import execute_values for bulk inserts


def load_sql_query(filepath):
    """
    Load a SQL query from a file.

    :param filepath: Path to the SQL file.
    :return: SQL query as a string.
    """
    with open(filepath, 'r') as f:
        return f.read()


def execute_nonquery(conn, sql, params=None, bulk=False):
    """
    Execute a SQL query, with optional support for bulk inserts.

    :param conn: Database connection object.
    :param sql: SQL query to execute.
    :param params: Optional parameters for the SQL query.
    :param bulk: Whether to execute a bulk insert.
    :return: None
    """
    with conn.cursor() as cursor:
        if bulk and params:
            # Use execute_values for bulk inserts
            execute_values(cursor, sql, params)
        elif params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)


def fetch_query_results(conn, sql, params=None):
    '''
    Fetch results from a SQL query.
    :param conn: Database connection object.
    :param sql: SQL query to execute.
    :param params: Optional parameters for the SQL query.
    :return: Query results.
    '''
    with conn.cursor() as cursor:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor.fetchall()


def fetch_query_single_result(conn, sql, params=None):
    '''
    Fetch a single result from a SQL query.
    :param conn: Database connection object.
    :param sql: SQL query to execute.
    :param params: Optional parameters for the SQL query.
    :return: Single query result.
    '''
    with conn.cursor() as cursor:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor.fetchone()
