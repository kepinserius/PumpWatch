-- Migration: 002_signals_and_outcomes.sql
-- Description: Add signals, alerts, and outcome tracking

CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    token_id INTEGER NOT NULL REFERENCES tokens(id),
    pool_id INTEGER REFERENCES pools(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    score INTEGER NOT NULL,
    score_components_json JSONB,
    feature_snapshot_json JSONB,
    risk_assessment_json JSONB,
    rules_version VARCHAR(16) NOT NULL DEFAULT '1.0',
    status VARCHAR(32) DEFAULT 'active',
    entry_price_usd NUMERIC(20, 10)
);

CREATE INDEX idx_signals_token_created ON signals(token_id, created_at DESC);
CREATE INDEX idx_signals_created_at ON signals(created_at DESC);
CREATE INDEX idx_signals_status ON signals(status);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER NOT NULL REFERENCES signals(id),
    channel VARCHAR(32) NOT NULL DEFAULT 'telegram',
    dedupe_key VARCHAR(256) NOT NULL,
    sent_at TIMESTAMPTZ,
    status VARCHAR(32) DEFAULT 'pending',
    attempt_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(dedupe_key)
);

CREATE INDEX idx_alerts_signal ON alerts(signal_id);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_created_at ON alerts(created_at DESC);

CREATE TABLE IF NOT EXISTS signal_outcomes (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER NOT NULL REFERENCES signals(id),
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    price_5m NUMERIC(20, 10),
    price_15m NUMERIC(20, 10),
    price_1h NUMERIC(20, 10),
    price_4h NUMERIC(20, 10),
    price_24h NUMERIC(20, 10),
    mfe NUMERIC(10, 4),
    mae NUMERIC(10, 4),
    return_5m NUMERIC(10, 4),
    return_15m NUMERIC(10, 4),
    return_1h NUMERIC(10, 4),
    return_4h NUMERIC(10, 4),
    return_24h NUMERIC(10, 4),
    return_net_5m NUMERIC(10, 4),
    return_net_15m NUMERIC(10, 4),
    return_net_1h NUMERIC(10, 4),
    return_net_4h NUMERIC(10, 4),
    return_net_24h NUMERIC(10, 4),
    liquidity_available BOOLEAN,
    data_available BOOLEAN DEFAULT true
);

CREATE INDEX idx_outcomes_signal ON signal_outcomes(signal_id);
CREATE INDEX idx_outcomes_checked_at ON signal_outcomes(checked_at DESC);

CREATE TABLE IF NOT EXISTS paper_trades (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER NOT NULL REFERENCES signals(id),
    entry_timestamp TIMESTAMPTZ NOT NULL,
    reference_entry_price NUMERIC(20, 10),
    simulated_entry_price NUMERIC(20, 10),
    position_size_usd NUMERIC(20, 2) DEFAULT 100.00,
    fee_assumption NUMERIC(6, 4) DEFAULT 0.01,
    slippage_assumption NUMERIC(6, 4) DEFAULT 0.02,
    exit_timestamp TIMESTAMPTZ,
    simulated_exit_price NUMERIC(20, 10),
    net_return NUMERIC(10, 4),
    status VARCHAR(32) DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_paper_trades_signal ON paper_trades(signal_id);
CREATE INDEX idx_paper_trades_status ON paper_trades(status);
CREATE INDEX idx_paper_trades_entry ON paper_trades(entry_timestamp DESC);
