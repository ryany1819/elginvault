import pytest
from db.connection import get_db_connection, close_db_connection

def test_get_db_connection(mocker):
    # Mock psycopg2.connect
    mock_connect = mocker.patch('psycopg2.connect', return_value='mock_connection')

    conn = get_db_connection()
    assert conn == 'mock_connection'
    mock_connect.assert_called_once()

def test_close_db_connection(mocker):
    mock_conn = mocker.Mock()
    close_db_connection(mock_conn)
    mock_conn.close.assert_called_once()