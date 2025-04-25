import pytest
from db.connection import get_db_connection, close_db_connection
from db.queries import load_sql_query, execute_nonquery, fetch_query_results
from tests.conftest import TEST_DB_NAME

@pytest.fixture(scope='function')
def setup_test_table():
    conn = get_db_connection()
    try:
        # Create a temporary test table
        create_table_sql = '''
        CREATE TEMP TABLE test_table (
            id SERIAL PRIMARY KEY,
            value VARCHAR(50)
        );
        '''
        execute_nonquery(conn, create_table_sql)
        yield conn  # Provide the connection to the test
    finally:
        close_db_connection(conn)

@pytest.mark.integration
def test_get_db_connection():
    conn = get_db_connection()
    assert conn is not None, 'Failed to establish database connection'
    with conn.cursor() as cursor:
        cursor.execute('SELECT current_database();')
        db_name = cursor.fetchone()[0]
    assert db_name == TEST_DB_NAME, f'Connected to wrong database: {db_name}. Expected: {TEST_DB_NAME}'
    close_db_connection(conn)

@pytest.mark.integration
def test_db_query_execution():
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT 1;')
            result = cursor.fetchone()
            assert result == (1,), 'Database query execution failed'
    finally:
        close_db_connection(conn)

@pytest.mark.integration
def test_load_sql_query():
    sql = load_sql_query('db/queries/get_stock_data_by_ticker_and_time_range.sql')
    assert sql is not None, 'Failed to load SQL query'
    with open('db/queries/get_stock_data_by_ticker_and_time_range.sql', 'r') as file:
        expected_sql = file.read()
    assert sql.strip() == expected_sql.strip(), 'SQL query content does not match expected content'

@pytest.mark.integration
def test_execute_select_query(setup_test_table):
    conn = setup_test_table
    insert_sql = '''
    INSERT INTO test_table (value)
    VALUES (%s);
    '''
    execute_nonquery(conn, insert_sql, params=('Test Value',))
    select_sql = 'SELECT value FROM test_table WHERE id = %s;'
    results = fetch_query_results(conn, select_sql, params=(1,))
    assert len(results) == 1, 'SELECT query failed'
    assert results[0] == ('Test Value',), 'SELECT query result mismatch'

@pytest.mark.integration
def test_execute_bulk_insert_query(setup_test_table):
    conn = setup_test_table
    bulk_insert_sql = '''
    INSERT INTO test_table (value)
    VALUES %s;
    '''
    data = [('Value 1',), ('Value 2',), ('Value 3',)]
    execute_nonquery(conn, bulk_insert_sql, data, bulk=True)
    # Verify the data was inserted
    select_sql = 'SELECT value FROM test_table ORDER BY id;'
    results = fetch_query_results(conn, select_sql)
    assert len(results) == 3, 'SELECT query failed'
    assert results == data, 'Bulk insert data mismatch'

@pytest.mark.integration
def test_all_tables_exist():
    required_tables = [
        'stock_data',
        'forex_data',
        'crypto_data',
        'stock_vault_catalog',
    ]
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            for table in required_tables:
                cursor.execute('''
                        SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = %s;
                    ''', (table,))
                result = cursor.fetchone()
                assert result is not None, f'Table ''{table}'' is missing in the database'
    finally:
        close_db_connection(conn)