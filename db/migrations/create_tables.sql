-- Create stock_data table
CREATE TABLE IF NOT EXISTS stock_data (
    timestamp TIMESTAMP NOT NULL,
    ticker TEXT NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    -- adjusted_close DOUBLE PRECISION,
    volume BIGINT
);

-- Convert stock_data to hypertable with partitioning
SELECT create_hypertable(
    'stock_data',
    time_column_name => 'timestamp',
    partitioning_column => 'ticker',
    number_partitions => 10,  -- Specify the number of partitions
    chunk_time_interval => INTERVAL '1 month'
);

-- Create forex_data table
CREATE TABLE IF NOT EXISTS forex_data (
    timestamp TIMESTAMP NOT NULL,
    pair TEXT NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION
);

-- Convert forex_data to hypertable with partitioning
SELECT create_hypertable(
    'forex_data',
    time_column_name => 'timestamp',
    partitioning_column => 'pair',
    number_partitions => 10,  -- Specify the number of partitions
    chunk_time_interval => INTERVAL '1 month'
);

-- Create crypto_data table
CREATE TABLE IF NOT EXISTS crypto_data (
    timestamp TIMESTAMP NOT NULL,
    pair TEXT NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION
);

-- Convert crypto_data to hypertable with partitioning
SELECT create_hypertable(
    'crypto_data',
    time_column_name => 'timestamp',
    partitioning_column => 'pair',
    number_partitions => 10,  -- Specify the number of partitions
    chunk_time_interval => INTERVAL '1 month'
);

-- Create stock_vault_catalog table
CREATE TABLE IF NOT EXISTS stock_vault_catalog (
    ticker TEXT NOT NULL PRIMARY KEY,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);