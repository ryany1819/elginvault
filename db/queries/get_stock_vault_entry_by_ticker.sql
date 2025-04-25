SELECT
    ticker,
    start_time,
    end_time,
    inserted_at
FROM stock_vault_catalog
WHERE ticker = %s;