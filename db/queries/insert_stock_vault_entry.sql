INSERT INTO stock_vault_catalog (
    ticker,
    start_time,
    end_time,
    inserted_at
) VALUES (
    %s, %s, %s, NOW()
);