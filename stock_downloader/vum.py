import os
import uuid
import csv
import asyncio
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

from elgin_api import import_stock_vault, check_task_status

CHUNK_SIZE = 30
DL_ROOT = os.path.join(os.path.dirname(__file__), 'downloads')

gen_merged_file_name = lambda symbol, starts, ends: f'{symbol}_{starts}-{ends}.csv'


class VaultUploadManager:
    pending_import_list = asyncio.Queue()
    pending_download_list = asyncio.Queue()
    importing_tasks = {}
    _lock = asyncio.Lock()

    @staticmethod
    async def initialize_orders(stocks: list[dict], chunksize: int = CHUNK_SIZE):
        for stock in stocks:
            await VaultUploadManager.initialize_single_order(stock, chunksize)

    @staticmethod
    async def initialize_single_order(stock, chunksize=CHUNK_SIZE):
        startdate = datetime.strptime(stock['starts'], '%Y-%m-%d')
        enddate = datetime.strptime(stock['ends'], '%Y-%m-%d')
        symbol, starts, ends = stock['symbol'], stock['starts'], stock['ends']
        order = {
            'id': uuid.uuid4(),
            'symbol': symbol,
            'starts': starts,
            'ends': ends,
            'csv_file': gen_merged_file_name(symbol, starts, ends),
            'status': '',
            'progress': 0,
            'chunks': [],
            'on_status_change': stock.get('on_status_change'),
        }
        sd = startdate
        while sd < enddate:
            ed = min(sd + timedelta(days=chunksize), enddate)
            chunk = {
                'sd': sd.strftime('%Y-%m-%d'),
                'ed': ed.strftime('%Y-%m-%d'),
                'status': 'pending',
                'file': f'{symbol}_{sd.strftime('%Y-%m-%d')}-{ed.strftime('%Y-%m-%d')}.chunk.csv',
            }
            order['chunks'].append(chunk)
            sd = ed + timedelta(days=1)
        await VaultUploadManager.pending_download_list.put(order)

    @staticmethod
    async def yf_to_csv_loop():
        while True:
            try:
                print('yf_to_csv_loop')
                order = await VaultUploadManager.pending_download_list.get()
                if order is None:
                    break
                VaultUploadManager.set_status(order, 'downloading')
                VaultUploadManager.download_yf_data_to_csv(order)
                VaultUploadManager.set_status(order, 'downloaded')
                await VaultUploadManager.pending_import_list.put(order)
            except Exception as e:
                print(f'Error in yf_to_csv_loop: {e}')

    @staticmethod
    async def import_loop():
        handlers = []
        semaphore = asyncio.Semaphore(10)
        while True:
            try:
                print('import_loop')
                order = await VaultUploadManager.pending_import_list.get()
                if order is None:
                    break

                async def handle_import(order):
                    async with semaphore:
                        rstd = import_stock_vault(
                            ticker=order['symbol'],
                            start_time=order['starts'],
                            end_time=order['ends'],
                            csv_file=os.path.join(DL_ROOT, order['csv_file']),
                        )
                        task_id = rstd['task_id']
                        VaultUploadManager.importing_tasks[task_id] = order
                        VaultUploadManager.set_status(order, 'importing')
                        await track_import(task_id)

                async def track_import(task_id):
                    while True:
                        await asyncio.sleep(1)
                        try:
                            rstd = check_task_status(task_id)
                            if 'Completed' in rstd['status']:
                                order = VaultUploadManager.importing_tasks[task_id]
                                VaultUploadManager.set_status(order, 'imported')
                                break
                            elif 'Failed' in rstd['status']:
                                raise Exception(
                                    f'Task {task_id} failed: {rstd['status']}'
                                )
                        except Exception as e:
                            print(f'Error in track_import: {e}')
                            order = VaultUploadManager.importing_tasks[task_id]
                            VaultUploadManager.set_status(order, 'import_failed')
                            raise e

                # Create a task for each order
                handlers.append(asyncio.create_task(handle_import(order)))
            except Exception as e:
                print(f'Error in import_loop: {e}')

        print('Waiting for all import tasks to complete...')
        results = await asyncio.gather(*handlers, return_exceptions=True)

        errors = [result for result in results if isinstance(result, Exception)]
        if errors:
            for error in errors:
                print(f'Error in handle_import: {error}')
        else:
            print('All import tasks completed successfully.')

    @staticmethod
    async def judge_loop():
        while True:
            await asyncio.sleep(1)
            async with VaultUploadManager._lock:  # Protect shared resource
                if (
                    VaultUploadManager.pending_download_list.empty()
                    and VaultUploadManager.pending_import_list.empty()
                    # and not VaultUploadManager.importing_tasks
                ):
                    print('All tasks completed.')
                    await VaultUploadManager.pending_download_list.put(None)
                    await VaultUploadManager.pending_import_list.put(None)
                    break

    @staticmethod
    def download_yf_data_to_csv(order):
        # create dir
        wd = os.path.join(DL_ROOT, str(order['id']))
        print('wd=', wd)
        os.makedirs(wd, exist_ok=True)
        # download chunks
        for i, chunk in enumerate(order['chunks'], start=1):
            VaultUploadManager.download_chunk(order['symbol'], wd, chunk)
            VaultUploadManager.set_progress(order, i / len(order['chunks']) * 100)
        # calls merge
        VaultUploadManager.merge_chunks_to_csv(order['csv_file'], wd, order['chunks'])

    '''
    perform yf download based on the dlp.chunk info
    * create chunk file (.csv)
    * update fields in dlp.chunk info
    '''

    @staticmethod
    def download_chunk(symbol, wd, chunk):
        try:
            df = yf.download(
                tickers=symbol,
                start=chunk['sd'],
                end=chunk['ed'],
                interval='1d',
                auto_adjust=False,
            )

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.reset_index()
            df = df.rename(
                columns={
                    'Date': 'timestamp',
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume',
                }
            )
            print('df.columns=', df.columns)
            df = df.drop(columns=['Adj Close'])
            df.insert(1, 'ticker', symbol)
            df = df[['timestamp', 'ticker', 'open', 'high', 'low', 'close', 'volume']]
            print('df=', df)
            df.to_csv(os.path.join(wd, chunk['file']), index=False, header=True)
            chunk['status'] = 'success'
        except Exception as e:
            chunk['status'] = 'failed'
            print(f'Error downloading chunk: {chunk}: {e}')

    @staticmethod
    def merge_chunks_to_csv(csv_file, wd, chunks):
        with open(os.path.join(DL_ROOT, csv_file), 'w', newline='') as f:
            writer = None
            for chunk in chunks:
                with open(os.path.join(wd, chunk['file']), 'r') as chunk_file:
                    reader = csv.reader(chunk_file)
                    if writer is None:
                        writer = csv.writer(f)
                    else:
                        next(reader)
                    writer.writerows(reader)
        print('Merged chunks into', csv_file)

        # delete the chunk folder
        for chunk in chunks:
            os.remove(os.path.join(wd, chunk['file']))
        os.rmdir(wd)

    @staticmethod
    async def start_task_loops():
        tasks = [
            VaultUploadManager.yf_to_csv_loop(),
            VaultUploadManager.import_loop(),
            VaultUploadManager.judge_loop(),
        ]
        print('Starting task loops...')
        await asyncio.gather(*tasks)
        print('Task loops stopped.')

    @staticmethod
    def _notify_state_change(order):
        callback = order.get('on_status_change')
        if callback:
            try:
                callback(order['status'], order['progress'])
            except Exception as e:
                print('Error in status change callback:', e)

    @staticmethod
    def set_status(order, status):
        order['status'] = status
        VaultUploadManager._notify_state_change(order)
        print(f'Status changed to {status} for order {order["id"]}')

    @staticmethod
    def set_progress(order, progress):
        order['progress'] = progress
        VaultUploadManager._notify_state_change(order)
        print('Progress changed to', progress, 'for order', order['id'])


if __name__ == '__main__':
    stocks = [
        {
            'symbol': 'AAPL',
            'starts': '2023-01-01',
            'ends': '2023-03-31',
            'on_status_change': lambda status, progress: print(status, progress),
        },
        {
            'symbol': 'GOOG',
            'starts': '2023-01-01',
            'ends': '2023-03-31',
            'on_status_change': lambda status, progress: print(status, progress),
        },
    ]

    async def main(stocks):
        await VaultUploadManager.initialize_orders(stocks)
        await VaultUploadManager.start_task_loops()

    try:
        asyncio.run(main(stocks=stocks))
    except KeyboardInterrupt:
        print('Program interrupted. Shutting down...')
