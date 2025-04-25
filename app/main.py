import uuid
import logging
import time
import pandas as pd
from typing import Optional
from io import StringIO
from fastapi import (
    FastAPI,
    HTTPException,
    BackgroundTasks,
    Form,
    UploadFile,
    File,
)
from fastapi.responses import StreamingResponse
from datetime import datetime
from pydantic import BaseModel
from typing import Generator
from app.models import StockData, StockCatalog
from app.repositories.exceptions import RepositoryException
from app.services.stock_data_service import prepare_records
from app.services.stock_vault_services import (
    import_stock_vault,
    remove_stock_vault,
    fetch_stock_vault_catalog_list,
    query_stock_vault_data,
    query_stock_vault_catalog_ticker,
)


class BulkInsertRequest(BaseModel):
    ticker: str
    start_time: str
    end_time: str
    csv_content: str


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('app.log')],
)
logging.info('Starting FastAPI application...')
app = FastAPI()
task_status = {}


def task_status_cleanup_loop(interval: int = 3600):
    timeout = datetime.now()
    while True:
        time.sleep(interval)
        for task_id, status in task_status.items():
            if status == 'Completed' or 'Failed' in status:
                del task_status[task_id]


def update_task_status(task_id: str, status: str):
    task_status[task_id] = status


def init_task_status(task_id: str):
    update_task_status(task_id, 'In Progress')


def process_bulk_insert_stock_data(
    ticker: str, start_time: str, end_time: str, csv_content: bytes, task_id: str
):
    try:
        # if not os.path.exists(req.csv_file):
        #     raise ValueError(f'CSV file does not exist: {req.csv_file}')
        # df = read_and_validate_csv(req.csv_file)
        # if df.empty:
        #     raise ValueError('CSV file is empty.')
        csv_string: str = csv_content.decode('utf-8')
        csv_io: StringIO = StringIO(csv_string)
        records = prepare_records(pd.read_csv(csv_io))
        logging.info(
            f'[Task {task_id}] Processing bulk insert for ticker: {ticker}, total records: {len(records)}'
        )
        import_stock_vault(ticker, start_time, end_time, records)
        update_task_status(task_id, 'Completed')
        logging.info(f'[Task {task_id}] Bulk insert completed successfully.')
    except ValueError as e:
        update_task_status(task_id, f'Failed: {e}')
        raise
    except RepositoryException as e:
        update_task_status(task_id, f'Failed: {e}')
        raise
    except Exception as e:
        logging.error(f'[Task {task_id}] Unexpected error: {e}', exc_info=True)
        update_task_status(task_id, 'Failed: Internal server error')
        raise


@app.get('/task_status/{task_id}')
async def get_taskstatus_taskid(task_id: str):
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail='Task ID not found.')
    return {'task_id': task_id, 'status': task_status[task_id]}


@app.get('/stock_data/{ticker}')
def get_stockdata_ticker(
    ticker: str, start_time: str = '2000-01-01', end_time: str = '2025-01-25'
):
    try:
        start_time_dt = datetime.strptime(start_time, '%Y-%m-%d')
        end_time_dt = datetime.strptime(end_time, '%Y-%m-%d')
        if start_time_dt > end_time_dt:
            raise ValueError('Start time must be before end time.')
        if not ticker:
            raise ValueError('Ticker symbol is required.')
        record_generator: Generator = query_stock_vault_data(
            ticker, start_time, end_time
        )

        def stream_data():
            count = 0
            yield '{"data": ['
            first = True
            record: StockData
            for record in record_generator:
                if not first:
                    yield ','
                first = False
                yield record.model_dump_json()
                count += 1
            yield f'], "count": {count}, "status": "success"}}'

        return StreamingResponse(stream_data(), media_type='application/json')
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f'Invalid date format: {e}')
    except RepositoryException as e:
        raise HTTPException(status_code=500, detail=f'Error retrieving stock data: {e}')


@app.post('/bulk_insert_stock_data')
async def post_bulkinsertstockdata2(
    ticker: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    csv_file: Optional[UploadFile] = File(None),
    background_tasks: BackgroundTasks = BackgroundTasks,
):
    try:
        # Check if the file is not provided
        if not csv_file or not csv_file.filename or csv_file.filename == "upload":
            raise HTTPException(status_code=400, detail='CSV file is required.')

        # Validate the file type
        if not csv_file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400, detail='Invalid file type. Only CSV files are allowed.'
            )

        # Validate other fields
        if not ticker:
            raise HTTPException(status_code=400, detail='"ticker" is required.')
        if not start_time or not end_time:
            raise HTTPException(
                status_code=400, detail='"start_time" and "end_time" are required.'
            )
        if start_time > end_time:
            raise HTTPException(
                status_code=400, detail='Start time must be before end time.'
            )

        csv_content = await csv_file.read()
        if not csv_content.strip():
            raise HTTPException(status_code=400, detail='CSV file is empty.')
        task_id = str(uuid.uuid4())
        init_task_status(task_id)
        background_tasks.add_task(
            process_bulk_insert_stock_data,
            ticker,
            start_time,
            end_time,
            csv_content,
            task_id,
        )
        return {'message': 'Stock data bulk insert started.', 'task_id': task_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f'Invalid request: {e}')
    except RepositoryException as e:
        raise HTTPException(
            status_code=500, detail=f'Error processing bulk insert: {e}'
        )


# old
@app.get('/stock/vault_catalog/all')
def get_stock_vaultcatalog_all():
    logging.info('Fetching all stock vault catalog...')
    try:
        record_generator = fetch_stock_vault_catalog_list()

        def stream_data():
            count = 0
            yield '{"data":['  # Start of the JSON object
            first = True
            for record in record_generator:
                if not first:
                    yield ','  # Add a comma between records
                first = False
                yield record.model_dump_json()  # Serialize each record to JSON
                count += 1
            yield f'], "count": {count}, "status": "success"}}'  # End of the JSON object

        return StreamingResponse(stream_data(), media_type="application/json")
    except RepositoryException as e:
        raise HTTPException(
            status_code=500, detail=f'Error retrieving stock catalog: {e}'
        )


# old
@app.get('/stock/vault_catalog/{ticker}')
def get_stock_vaultcatalog_ticker(ticker: str):
    logging.info(f'Fetching stock vault catalog for ticker: {ticker}')
    try:
        if not ticker:
            raise ValueError('Ticker symbol is required.')
        result = query_stock_vault_catalog_ticker(ticker)

        if result:
            return {
                "data": result.model_dump(),  # Serialize the StockCatalog object
                "message": "Stock catalog retrieved successfully",
                "status": "success",
            }
        else:
            return {
                "data": None,
                "message": "No stock catalog found for the given ticker",
                "status": "success",
            }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f'Invalid ticker symbol: {e}')
    except RepositoryException as e:
        raise HTTPException(
            status_code=500, detail=f'Error retrieving stock catalog: {e}'
        )


# v2 POST /stock_vault/import
@app.post('/stock_vault/import')
async def post_stockvault_import(
    ticker: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    csv_file: Optional[UploadFile] = File(None),
    background_tasks: BackgroundTasks = BackgroundTasks,
):
    try:
        # Check if the file is not provided
        if not csv_file or not csv_file.filename or csv_file.filename == "upload":
            raise HTTPException(status_code=400, detail='CSV file is required.')

        # Validate the file type
        if not csv_file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400, detail='Invalid file type. Only CSV files are allowed.'
            )

        # Validate other fields
        if not ticker:
            raise HTTPException(status_code=400, detail='"ticker" is required.')
        if not start_time or not end_time:
            raise HTTPException(
                status_code=400, detail='"start_time" and "end_time" are required.'
            )
        if start_time > end_time:
            raise HTTPException(
                status_code=400, detail='Start time must be before end time.'
            )
        csv_content = await csv_file.read()
        if not csv_content.strip():
            raise HTTPException(status_code=400, detail='CSV file is empty.')
        # Check if stock catalog already exists
        existing_catalog = query_stock_vault_catalog_ticker(ticker)
        if existing_catalog:
            remove_stock_vault(ticker)
        task_id = str(uuid.uuid4())
        init_task_status(task_id)
        background_tasks.add_task(
            process_bulk_insert_stock_data,
            ticker,
            start_time,
            end_time,
            csv_content,
            task_id,
        )
        return {'message': 'Stock data bulk insert started.', 'task_id': task_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f'Invalid request: {e}')
    except RepositoryException as e:
        raise HTTPException(
            status_code=500, detail=f'Error processing bulk insert: {e}'
        )


# v2 DELETE /stock_vault/{ticker}
@app.delete('/stock_vault/{ticker}')
def delete_stockvault_ticker(ticker: str):
    try:
        return remove_stock_vault(ticker)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f'Invalid ticker symbol: {e}')
    except RepositoryException as e:
        raise HTTPException(
            status_code=500, detail=f'Error deleting stock vault catalog: {e}'
        )


# v2 GET /stock_vault/catalog_all
@app.get('/stock_vault/catalog_all')
def get_stockvault_catalog():
    logging.info('Fetching all stock vault catalog...')
    return get_stock_vaultcatalog_all()


# v2 GET /stock_vault/catalog/{ticker}
@app.get('/stock_vault/catalog/{ticker}')
def get_stockvault_catalog_ticker(ticker: str):
    return get_stock_vaultcatalog_ticker(ticker)


# v2 GET /stock_vault/data/{ticker}
@app.get('/stock_vault/data/{ticker}')
def get_stockvault_data_ticker(ticker: str):
    return get_stockdata_ticker(ticker)
