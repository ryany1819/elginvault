import pytest
import time
from fastapi.testclient import TestClient

from app.main import app
from db.connection import get_db_connection, close_db_connection
from db.queries import load_sql_query

'''
test plan:
- test '/bulk_insert_stock_data'
- test '/stock_data/{ticker}'
'''
client = TestClient(app)


@pytest.fixture(scope='module')
def setup_module():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                '''
                           DELETE FROM stock_vault_catalog;
                           '''
            )
        conn.commit()
        close_db_connection(conn)
    # yield
    # with get_db_connection() as conn:
    #     with conn.cursor() as cursor:
    #         cursor.execute('''
    #                        DELETE FROM stock_vault_catalog;
    #                        ''')
    #     conn.commit()
    #     close_db_connection(conn)


@pytest.mark.integration
def test_bulk_insert_stock_data_valid():
    response = client.post(
        '/bulk_insert_stock_data',
        data={
            'ticker': 'AAPL',
            'start_time': '2023-01-01',
            'end_time': '2023-01-02',
        },
        files={
            'csv_file': (
                'valid_stock_data.csv',
                open('tests/data/valid_stock_data.csv', 'rb'),
            ),
        },
    )
    task_id = response.json()['task_id']
    assert response.status_code == 200
    assert response.json()['message'] == 'Stock data bulk insert started.'

    elapsed_time = 0
    interval = 1
    timeout = 10
    while elapsed_time < timeout:
        response = client.get(f'/task_status/{task_id}')
        assert response.status_code == 200
        status_data = response.json()
        if status_data['status'] == 'Completed':
            break
        time.sleep(interval)
        elapsed_time += interval
    else:
        pytest.fail(f'Task {task_id} did not complete within {timeout} seconds')

    assert (
        status_data['status'] == 'Completed'
    ), f'Expected status "Completed", got {status_data["status"]}'


@pytest.mark.integration
def test_bulk_insert_stock_data_invalid():
    response = client.post(
        '/bulk_insert_stock_data',
        data={
            'ticker': 'AAPL',
            'start_time': '2023-01-01',
            'end_time': '2023-01-02',
        },
        files={'csv_file': ''},
    )
    assert response.status_code == 400, 'Expected 400 status code for invalid CSV file'
    assert response.json()['detail'] == 'CSV file is required.'

    # Test with no file uploaded
    response = client.post(
        '/bulk_insert_stock_data',
        data={
            'ticker': 'AAPL',
            'start_time': '2023-01-01',
            'end_time': '2023-01-02',
        },
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "CSV file is required."}


@pytest.mark.integration
def test_get_stock_data_valid():
    response = client.get(
        '/stock_data/AAPL',
        params={
            'start_time': '2023-01-01',
            'end_time': '2023-01-02',
        },
    )
    data = response.json()
    assert response.status_code == 200
    assert 'data' in data, 'Expected "data" key in response'
    assert data['ticker'] == 'AAPL'
    assert data['start_time'] == '2023-01-01'
    assert data['end_time'] == '2023-01-02'


@pytest.mark.integration
def test_get_stock_data_invalid_date():
    response = client.get(
        '/stock_data/AAPL',
        params={
            'start_time': 'invalid_date',
            'end_time': '2023-01-02',
        },
    )
    assert (
        response.status_code == 400
    ), 'Expected 400 status code for invalid date format'


@pytest.mark.integration
def test_task_status_invalid():
    response = client.get('/task_status/invalid-task-id')
    assert response.status_code == 404, 'Expected 404 status code for invalid task ID'
    data = response.json()
    assert data['detail'] == 'Task ID not found.'


@pytest.mark.integration
def test_get_all_stock_vault_catalog_valid():
    response = client.get('/stock/vault_catalog/all')
    assert response.status_code == 200
    data = response.json()
    assert 'data' in data, 'Expected ' 'data' ' key in response'
    assert 'count' in data, 'Expected ' 'count' ' key in response'
    assert len(data['data']) > 0, 'Expected at least one catalog entry'


@pytest.mark.integration
def test_get_stock_vault_entry_by_ticker_valid():
    response = client.get('/stock/vault_catalog/AAPL')
    assert response.status_code == 200
    data = response.json()
    assert 'ticker' in data, 'Expected ' 'ticker' ' key in response'
    assert 'data' in data, 'Expected "data" key in response'
    assert 'count' in data, 'Expected "count" key in response'
    assert data['count'] == 1, 'Expected count to be 1 for valid ticker'


@pytest.mark.integration
def test_get_stock_catalog_by_ticker_invalid():
    response = client.get('/stock/vault_catalog/INVALID_TICKER')
    assert response.status_code == 404
    print(response, response.json())
    assert (
        response.json()['detail']
        == 'No stock catalog found for the given ticker: INVALID_TICKER'
    )


@pytest.mark.integration
def test_get_stock_catalog_by_ticker_empty_ticker():
    response = client.get('/stock_catalog/')
    assert response.status_code == 404, 'Expected 404 status code for empty ticker'
