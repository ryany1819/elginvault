from pydantic import BaseModel
from datetime import datetime

class StockData(BaseModel):
    timestamp: datetime
    ticker: str
    open: float
    high: float
    low: float
    close: float
    volume: int

class StockCatalog(BaseModel):
    ticker: str
    start_time: datetime
    end_time: datetime
    inserted_at: datetime
