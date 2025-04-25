import os
import pytest
import psycopg2
from db.connection import get_db_params, get_db_connection, close_db_connection

TEST_DB_NAME = 'test_db'

@pytest.fixture(scope='session', autouse=True)
def setup_testing_databse():
    '''
    Fixture to create and tear down a test database.
    '''
    os.environ['DB_DBNAME'] = TEST_DB_NAME

    # Attempt to connect to the 'postgres' database, fallback to 'template1' if unavailable
    try:
        conn = psycopg2.connect(
            dbname="postgres",  # Default database
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "password"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )
    except psycopg2.OperationalError:
        print("Warning: 'postgres' database not found. Falling back to 'template1'.")
        conn = psycopg2.connect(
            dbname="template1",  # Fallback database
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "password"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )

    conn.autocommit = True
    try:
        with conn.cursor() as cursor:
            # Check if the test database exists
            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{TEST_DB_NAME}'")
            db_exists = cursor.fetchone()
            if db_exists:
                # Drop and recreate the test database
                cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
            cursor.execute(f"CREATE DATABASE {TEST_DB_NAME}")

            # Connect to the test database and run migrations
            assert os.getenv('DB_DBNAME') == TEST_DB_NAME, f'DB_DBNAME should be set to {TEST_DB_NAME}'
            test_conn = get_db_connection()
            try:
                with test_conn.cursor() as test_cursor:
                    with open('db/migrations/create_tables.sql', 'r') as f:
                        test_cursor.execute(f.read())
                    test_conn.commit()
            finally:
                close_db_connection(test_conn)
    finally:
        close_db_connection(conn)

    yield

    # Teardown
    conn = psycopg2.connect(
        dbname="postgres",  # Default database
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "password"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
    )
    conn.autocommit = True
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
    finally:
        conn.close()

# @pytest.fixture(scope='function', autouse=True)
# def use_testing_database(monkeypatch):
#     '''
#     This fixture sets the environment variables to use the testing database.
#     '''
#     monkeypatch.setenv('DB_DBNAME', TEST_DB_NAME)