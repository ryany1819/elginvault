import pandas as pd
from app.models import StockData

def read_and_validate_csv(csv_file: str):
    df = pd.read_csv(csv_file)
    if df.empty:
        raise ValueError(f'CSV file is empty: {csv_file}')
    if 'timestamp' not in df.columns or 'ticker' not in df.columns:
        raise ValueError('CSV file must contain "timestamp" and "ticker" columns.')
    return df
    
def prepare_records(df: pd.DataFrame) -> list[StockData]:
    records = []
    for index, record in enumerate(df.to_dict(orient='records')):
        stock_data = StockData(**record)
        records.append(stock_data)
    return records