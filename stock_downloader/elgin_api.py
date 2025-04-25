import requests
import os


baseurl = 'http://a5sp14:8001'
apiurls = {
    'get_all_stockvault_catalog': lambda baseurl: f'{baseurl}/stock_vault/catalog_all',
    'delete_stockvault_ticker': lambda baseurl, ticker: f'{baseurl}/stock_vault/{ticker}',
    'import_stockvault_ticker_timerange': lambda baseurl: f'{baseurl}/stock_vault/import',
}


def load_stocks_catalog():
    res = requests.get(apiurls['get_all_stockvault_catalog'](baseurl))
    if res.status_code != 200:
        return None
    return [
        {
            'symbol': x['ticker'],
            'starts_on': x['start_time'],
            'ends_on': x['end_time'],
            'downloaded_at': x['inserted_at'],
        }
        for x in res.json()['data']
    ]


def delete_stock_vault_ticker(ticker):
    print('ticker=', ticker)
    res = requests.delete(apiurls['delete_stockvault_ticker'](baseurl, ticker))
    res.raise_for_status()
    return res.json()


def import_stock_vault(ticker, start_time: str, end_time: str, csv_file: str):
    if not ticker:
        raise ValueError('Ticker is required.')
    if not start_time or not end_time:
        raise ValueError('Start time and end time are required.')
    if start_time > end_time:
        raise ValueError('Start time must be before end time.')

    if not os.path.exists(csv_file):
        raise FileNotFoundError(f'CSV file: {csv_file} does not exist.')

    with open(csv_file, 'rb') as file:
        res = requests.post(
            apiurls['import_stockvault_ticker_timerange'](baseurl),
            data={
                'ticker': ticker,
                'start_time': start_time,
                'end_time': end_time,
            },
            files={'csv_file': file},
        )
        res.raise_for_status()
        return res.json()


def check_task_status(task_id):
    res = requests.get(f'{baseurl}/task_status/{task_id}')
    res.raise_for_status()
    return res.json()
