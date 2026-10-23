-- Migration: 001_initial_schema.sql
-- Description: Create initial tables for tokens, pools, and market snapshots

CREATE TABLE IF NOT EXISTS tokens (
    id SERIAL PRIMARY KEY,
    chain VARCHAR(32) NOT NULL,
    address VARCHAR(128) NOT NULL,
    symbol VARCHAR(64),
    name VARCHAR(256),
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata_json JSONB,
    UNIQUE(chain, address)
);

CREATE INDEX idx_tokens_chain_address ON tokens(chain, address);
CREATE INDEX idx_tokens_first_seen ON tokens(first_seen_at DESC);

CREATE TABLE IF NOT EXISTS pools (
    id SERIAL PRIMARY KEY,
    chain VARCHAR(32) NOT NULL,
    pool_address VARCHAR(128) NOT NULL,
    base_token_address VARCHAR(128) NOT NULL,
    quote_token_address VARCHAR(128) NOT NULL,
    dex_id VARCHAR(64),
    created_at TIMESTAMPTZ,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(chain, pool_address)
);

CREATE INDEX idx_pools_chain_pool ON pools(chain, pool_address);
CREATE INDEX idx_pools_base_token ON pools(base_token_address);
CREATE INDEX idx_pools_created_at ON pools(created_at DESC);

CREATE TABLE IF NOT EXISTS market_snapshots (
    id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES tokens(id),
    pool_id INTEGER REFERENCES pools(id),
    observed_at TIMESTAMPTZ NOT NULL,
    source VARCHAR(64) NOT NULL,
    price_usd NUMERIC(20, 10),
    liquidity_usd NUMERIC(20, 2),
    volume_5m NUMERIC(20, 2),
    volume_1h NUMERIC(20, 2),
    volume_6h NUMERIC(20, 2),
    volume_24h NUMERIC(20, 2),
    price_change_5m NUMERIC(10, 4),
    price_change_1h NUMERIC(10, 4),
    price_change_6h NUMERIC(10, 4),
    price_change_24h NUMERIC(10, 4),
    buys_5m INTEGER,
    buys_1h INTEGER,
    buys_6h INTEGER,
    buys_24h INTEGER,
    sells_5m INTEGER,
    sells_1h INTEGER,
    sells_6h INTEGER,
    sells_24h INTEGER,
    raw_data_ref JSONB,
    data_quality_status VARCHAR(32) DEFAULT 'valid',
    CHECK (token_id IS NOT NULL OR pool_id IS NOT NULL)
);

CREATE INDEX idx_snapshots_token_observed ON market_snapshots(token_id, observed_at DESC);
CREATE INDEX idx_snapshots_pool_observed ON market_snapshots(pool_id, observed_at DESC);
CREATE INDEX idx_snapshots_observed_at ON market_snapshots(observed_at DESC);
CREATE INDEX idx_snapshots_source ON market_snapshots(source);
