-- Migration: 003_post_mvp_features.sql
-- Description: Post-MVP features - Historical Archive, Advanced Alerts, Analytics, Backtest

BEGIN;

-- ============================================================================
-- Feature 1: Historical Data Archive
-- ============================================================================

-- Archive momentum score snapshots
CREATE TABLE IF NOT EXISTS momentum_snapshots (
    id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES tokens(id) ON DELETE CASCADE,
    pool_id INTEGER REFERENCES pools(id) ON DELETE SET NULL,
    snapshot_at TIMESTAMPTZ NOT NULL,
    momentum_score NUMERIC(5,2) NOT NULL,
    score_components JSONB NOT NULL,
    features JSONB,
    data_coverage NUMERIC(5,4),
    rules_version VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_momentum_snap_token_time ON momentum_snapshots(token_id, snapshot_at DESC);
CREATE INDEX idx_momentum_snap_time ON momentum_snapshots(snapshot_at DESC);

-- Archive risk assessment snapshots
CREATE TABLE IF NOT EXISTS risk_snapshots (
    id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES tokens(id) ON DELETE CASCADE,
    pool_id INTEGER REFERENCES pools(id) ON DELETE SET NULL,
    snapshot_at TIMESTAMPTZ NOT NULL,
    risk_level VARCHAR(50) NOT NULL,
    hard_block BOOLEAN DEFAULT FALSE,
    flags JSONB NOT NULL,
    coverage NUMERIC(5,4),
    rules_version VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_risk_snap_token_time ON risk_snapshots(token_id, snapshot_at DESC);
CREATE INDEX idx_risk_snap_time ON risk_snapshots(snapshot_at DESC);

-- ============================================================================
-- Feature 2: Advanced Alert System
-- ============================================================================

-- User-defined alert rules (per token atau global)
CREATE TABLE IF NOT EXISTS alert_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    token_id INTEGER REFERENCES tokens(id) ON DELETE CASCADE,
    is_global BOOLEAN DEFAULT FALSE,
    momentum_threshold NUMERIC(5,2),
    risk_level_max VARCHAR(50),
    min_liquidity_usd NUMERIC(20,2),
    cooldown_minutes INTEGER DEFAULT 60,
    priority VARCHAR(20) DEFAULT 'normal',
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Cooldown tracking per pair
CREATE TABLE IF NOT EXISTS alert_cooldowns (
    id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES tokens(id) ON DELETE CASCADE,
    pool_id INTEGER REFERENCES pools(id) ON DELETE CASCADE,
    alert_rule_id INTEGER REFERENCES alert_rules(id) ON DELETE CASCADE,
    last_alert_sent_at TIMESTAMPTZ NOT NULL,
    next_alert_allowed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(token_id, pool_id, alert_rule_id)
);

CREATE INDEX idx_alert_cooldowns_token_pool ON alert_cooldowns(token_id, pool_id);
CREATE INDEX idx_alert_cooldowns_next_allowed ON alert_cooldowns(next_alert_allowed_at);

-- ============================================================================
-- Feature 3: Dashboard Analytics
-- ============================================================================

-- Agregasi momentum/risk per timeframe
CREATE TABLE IF NOT EXISTS momentum_aggregates (
    id SERIAL PRIMARY KEY,
    time_bucket TIMESTAMPTZ NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    avg_momentum_score NUMERIC(5,2),
    median_momentum_score NUMERIC(5,2),
    high_momentum_count INTEGER,
    medium_momentum_count INTEGER,
    low_momentum_count INTEGER,
    avg_liquidity_usd NUMERIC(20,2),
    total_tokens_scanned INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(time_bucket, timeframe)
);

CREATE TABLE IF NOT EXISTS risk_aggregates (
    id SERIAL PRIMARY KEY,
    time_bucket TIMESTAMPTZ NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    low_risk_count INTEGER,
    medium_risk_count INTEGER,
    high_risk_count INTEGER,
    hard_blocked_count INTEGER,
    avg_risk_coverage NUMERIC(5,4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(time_bucket, timeframe)
);

CREATE INDEX idx_momentum_agg_time ON momentum_aggregates(time_bucket DESC);
CREATE INDEX idx_risk_agg_time ON risk_aggregates(time_bucket DESC);

-- ============================================================================
-- Feature 4: Backtesting Engine
-- ============================================================================

-- Backtest runs (configuration + metadata)
CREATE TABLE IF NOT EXISTS backtest_runs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    strategy_config JSONB NOT NULL,
    fee_percent NUMERIC(5,4) DEFAULT 0.01,
    slippage_percent NUMERIC(5,4) DEFAULT 0.005,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    summary_stats JSONB
);

-- Backtest trades (simulated)
CREATE TABLE IF NOT EXISTS backtest_trades (
    id SERIAL PRIMARY KEY,
    backtest_run_id INTEGER REFERENCES backtest_runs(id) ON DELETE CASCADE,
    signal_id INTEGER REFERENCES signals(id),
    token_id INTEGER REFERENCES tokens(id),
    entry_timestamp TIMESTAMPTZ NOT NULL,
    entry_price NUMERIC(20,10),
    exit_timestamp TIMESTAMPTZ,
    exit_price NUMERIC(20,10),
    position_size_usd NUMERIC(20,2),
    gross_return NUMERIC(10,4),
    net_return NUMERIC(10,4),
    fees_paid NUMERIC(20,2),
    slippage_impact NUMERIC(20,2),
    exit_reason VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_backtest_trades_run ON backtest_trades(backtest_run_id);
CREATE INDEX idx_backtest_trades_signal ON backtest_trades(signal_id);

COMMIT;
