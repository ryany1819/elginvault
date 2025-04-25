import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def mock_csv_file(tmp_path):
    # Create a temporary CSV file with mock data
    csv_file = tmp_path / 'test.csv'
    csv_file.write_text(
        'timestamp,ticker,open,high,low,close,volume\n'
        '2023-01-01,AAPL,100.0,110.0,90.0,105.0,10000\n'
        '2023-01-02,AAPL,105.0,115.0,95.0,110.0,15000\n'
    )
    return str(csv_file)


@pytest.mark.asyncio
async def test_bulk_insert_stock_data(mocker, mock_csv_file):
    # Mock the process_bulk_insert_stock_data function
    mock_process_bulk_insert_stock_data = mocker.patch(
        'app.main.process_bulk_insert_stock_data', return_value=None
    )

    # Use FastAPI's TestClient for testing
    with TestClient(app) as client:
        response = client.post(
            '/bulk_insert_stock_data',
            data={
                'ticker': 'AAPL',
                'start_time': '2023-01-01',
                'end_time': '2023-01-02',
            },
            files={'csv_file': ('test.csv', open(mock_csv_file, 'rb'))},
        )

    # Assert the response
    assert response.status_code == 200
    assert response.json()['message'] == 'Stock data bulk insert started.'
    assert response.json()['task_id'] is not None
    mock_process_bulk_insert_stock_data.assert_called_once()
    assert 'task_id' in response.json()
