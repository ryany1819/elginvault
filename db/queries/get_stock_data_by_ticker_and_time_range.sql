SELECT *
FROM stock_data
WHERE ticker = %s
    AND timestamp BETWEEN %s AND %s
ORDER BY timestamp;