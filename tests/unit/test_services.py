import pytest
import pandas as pd
from datetime import datetime

from app.services.stock_data_service import read_and_validate_csv, prepare_records
from app.models import StockData

def test_read_and_validate_csv(mocker):
    # Mock pandas.read_csv
    mock_read_csv = mocker.patch('pandas.read_csv', return_value=pd.DataFrame({
        'timestamp': ['2023-01-01'],
        'ticker': ['AAPL'],
    }))
    df = read_and_validate_csv('test.csv')
    assert not df.empty
    assert 'timestamp' in df.columns
    assert 'ticker' in df.columns

def test_prepare_records():
    df = pd.DataFrame({
        'timestamp': ['2023-01-01'],
        'ticker': ['AAPL'],
        'open': [150.0],
        'high': [155.0],
        'low': [149.0],
        'close': [154.0],
        'volume': [1000],
    })
    records = prepare_records(df)
    assert len(records) == 1
    assert records[0] == StockData(
        timestamp=datetime.strptime('2023-01-01', '%Y-%m-%d'),
        ticker='AAPL',
        open=150.0,
        high=155.0,
        low=149.0,
        close=154.0,
        volume=1000,
    )