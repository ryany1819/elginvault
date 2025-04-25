SELECT
    ticker,
    start_time,
    end_time,
    inserted_at
FROM stock_vault_catalog
ORDER BY inserted_at DESC;
