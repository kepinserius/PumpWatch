# Tech Spec: Post-MVP Features

**Dokumen:** Post-MVP Features\
**Tanggal:** 2026-10-27\
**Status:** Draft untuk implementasi\
**Scope:** 4 fitur tambahan setelah MVP selesai

## 1. Overview

Implementasi 4 fitur post-MVP untuk PumpWatch:
1. Backtesting engine dengan fee/slippage
2. Dashboard analytics (trend momentum/risk per timeframe)
3. Historical data archive (snapshot momentum/risk berkala)
4. Advanced alert system (per-token threshold, per-pair cooldown)

## 2. Tech Stack (Existing)

- Backend: Python 3.12+ + FastAPI
- Database: PostgreSQL
- Frontend: Next.js 15 + TypeScript
- Charts: Recharts
- Existing tables: tokens, pools, market_snapshots, signals, alerts

## 3. Feature Breakdown

### Feature 1: Backtesting Engine

**Tujuan:** Uji rule-based strategy dengan historis data, hitung performance metrics dengan fee/slippage realistis.

#### Database Schema Changes

```sql
-- Tabel untuk backtest configuration
CREATE TABLE backtest_runs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    strategy_config JSONB NOT NULL,
    fee_percent DECIMAL(5,4) DEFAULT 0.01,
    slippage_percent DECIMAL(5,4) DEFAULT 0.005,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    summary_stats JSONB
);

-- Tabel untuk backtest trades (simulated)
CREATE TABLE backtest_trades (
    id SERIAL PRIMARY KEY,
    backtest_run_id INTEGER REFERENCES backtest_runs(id) ON DELETE CASCADE,
    signal_id INTEGER REFERENCES signals(id),
    token_id INTEGER REFERENCES tokens(id),
    entry_timestamp TIMESTAMP NOT NULL,
    entry_price DECIMAL(20,10),
    exit_timestamp TIMESTAMP,
    exit_price DECIMAL(20,10),
    position_size_usd DECIMAL(20,2),
    gross_return DECIMAL(10,4),
    net_return DECIMAL(10,4),
    fees_paid DECIMAL(20,2),
    slippage_impact DECIMAL(20,2),
    exit_reason VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_backtest_trades_run ON backtest_trades(backtest_run_id);
CREATE INDEX idx_backtest_trades_signal ON backtest_trades(signal_id);
```

#### Backend Implementation

**File:** `backend/src/pumpwatch/services/backtest.py`

```python
class BacktestEngine:
    def __init__(self, db: Database, config: BacktestConfig):
        self.db = db
        self.config = config
    
    async def run_backtest(
        self,
        start_date: datetime,
        end_date: datetime,
        strategy_params: dict
    ) -> BacktestResult:
        """
        Jalankan backtest untuk periode tertentu.
        1. Ambil semua signals dalam periode
        2. Untuk setiap signal, cari exit berdasarkan rules
        3. Hitung PnL dengan fee/slippage
        4. Aggregate metrics
        """
        pass
    
    async def calculate_metrics(self, trades: list[BacktestTrade]) -> dict:
        """
        Return:
        - total_trades
        - win_rate
        - avg_return
        - sharpe_ratio (simplified)
        - max_drawdown
        - total_fees
        - total_slippage
        """
        pass
```

**File:** `backend/src/pumpwatch/api/backtest_router.py`

```python
@router.post("/api/v1/backtest/run")
async def create_backtest_run(config: BacktestRunRequest):
    """Buat dan jalankan backtest baru"""
    pass

@router.get("/api/v1/backtest/runs")
async def list_backtest_runs(limit: int = 20, offset: int = 0):
    """List semua backtest runs dengan pagination"""
    pass

@router.get("/api/v1/backtest/runs/{run_id}")
async def get_backtest_result(run_id: int):
    """Detail hasil backtest + metrics"""
    pass

@router.get("/api/v1/backtest/runs/{run_id}/trades")
async def get_backtest_trades(run_id: int, limit: int = 50):
    """List trades dari backtest tertentu"""
    pass
```

#### Frontend Implementation

**File:** `frontend/app/backtest/page.tsx`

- Form untuk konfigurasi backtest (date range, strategy params, fee/slippage)
- List backtest runs dengan status
- Detail view: metrics cards + trades table
- Chart: equity curve, drawdown

#### Exit Strategy Rules

Default exit conditions (configurable):
1. Time-based: 1h, 4h, atau 24h setelah entry
2. Profit target: +20%, +50%, +100%
3. Stop-loss: -15%
4. Trailing stop: -10% dari peak

---

### Feature 2: Dashboard Analytics

**Tujuan:** Visualisasi trend momentum/risk agregat, top tokens per kategori, time-series analysis.

#### Database Schema Changes

```sql
-- Agregasi momentum/risk per timeframe
CREATE TABLE momentum_aggregates (
    id SERIAL PRIMARY KEY,
    time_bucket TIMESTAMP NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    avg_momentum_score DECIMAL(5,2),
    median_momentum_score DECIMAL(5,2),
    high_momentum_count INTEGER,
    medium_momentum_count INTEGER,
    low_momentum_count INTEGER,
    avg_liquidity_usd DECIMAL(20,2),
    total_tokens_scanned INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(time_bucket, timeframe)
);

CREATE TABLE risk_aggregates (
    id SERIAL PRIMARY KEY,
    time_bucket TIMESTAMP NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    low_risk_count INTEGER,
    medium_risk_count INTEGER,
    high_risk_count INTEGER,
    hard_blocked_count INTEGER,
    avg_risk_coverage DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(time_bucket, timeframe)
);

CREATE INDEX idx_momentum_agg_time ON momentum_aggregates(time_bucket DESC);
CREATE INDEX idx_risk_agg_time ON risk_aggregates(time_bucket DESC);
```

#### Backend Implementation

**File:** `backend/src/pumpwatch/services/analytics.py`

```python
class AnalyticsService:
    async def compute_aggregates(self, timeframe: str = '1h'):
        """
        Hitung agregat momentum/risk untuk window terakhir.
        Timeframe: 1h, 4h, 24h
        Dipanggil oleh background worker setiap interval.
        """
        pass
    
    async def get_momentum_trend(
        self,
        timeframe: str,
        hours: int = 24
    ) -> list[MomentumAggregate]:
        """Return time-series momentum aggregates"""
        pass
    
    async def get_top_tokens(
        self,
        category: str,
        limit: int = 10
    ) -> list[TokenWithScore]:
        """
        Category: high_momentum, watchlist, high_liquidity, new_pools
        """
        pass
```

**File:** `backend/src/pumpwatch/api/analytics_router.py`

```python
@router.get("/api/v1/analytics/momentum/trend")
async def get_momentum_trend(timeframe: str = '1h', hours: int = 24):
    """Momentum trend time-series"""
    pass

@router.get("/api/v1/analytics/risk/trend")
async def get_risk_trend(timeframe: str = '1h', hours: int = 24):
    """Risk distribution trend"""
    pass

@router.get("/api/v1/analytics/top-tokens")
async def get_top_tokens(category: str, limit: int = 10):
    """Top tokens per kategori"""
    pass

@router.get("/api/v1/analytics/overview")
async def get_analytics_overview():
    """
    Dashboard overview:
    - Total scanned last 24h
    - Avg momentum score
    - Risk distribution
    - Top movers
    """
    pass
```

#### Frontend Implementation

**File:** `frontend/app/analytics/page.tsx`

Sections:
1. Overview cards (24h stats)
2. Momentum trend chart (line chart, configurable timeframe)
3. Risk distribution chart (stacked area atau bar chart)
4. Top tokens table per kategori (tabs: high momentum, watchlist, new pools)
5. Heatmap: momentum vs risk (scatter plot)

---

### Feature 3: Historical Data Archive

**Tujuan:** Simpan snapshot momentum/risk setiap interval untuk analisis historis dan backtest yang lebih akurat.

#### Database Schema Changes

```sql
-- Archive momentum score snapshots
CREATE TABLE momentum_snapshots (
    id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES tokens(id) ON DELETE CASCADE,
    pool_id INTEGER REFERENCES pools(id) ON DELETE SET NULL,
    snapshot_at TIMESTAMP NOT NULL,
    momentum_score DECIMAL(5,2) NOT NULL,
    score_components JSONB NOT NULL,
    features JSONB,
    data_coverage DECIMAL(5,4),
    rules_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Archive risk assessment snapshots
CREATE TABLE risk_snapshots (
    id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES tokens(id) ON DELETE CASCADE,
    pool_id INTEGER REFERENCES pools(id) ON DELETE SET NULL,
    snapshot_at TIMESTAMP NOT NULL,
    risk_level VARCHAR(50) NOT NULL,
    hard_block BOOLEAN DEFAULT FALSE,
    flags JSONB NOT NULL,
    coverage DECIMAL(5,4),
    rules_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_momentum_snap_token_time ON momentum_snapshots(token_id, snapshot_at DESC);
CREATE INDEX idx_risk_snap_token_time ON risk_snapshots(token_id, snapshot_at DESC);
CREATE INDEX idx_momentum_snap_time ON momentum_snapshots(snapshot_at DESC);
CREATE INDEX idx_risk_snap_time ON risk_snapshots(snapshot_at DESC);
```

#### Backend Implementation

**File:** `backend/src/pumpwatch/services/archiver.py`

```python
class DataArchiver:
    def __init__(self, db: Database):
        self.db = db
        self.snapshot_interval_minutes = settings.archive_interval_minutes
    
    async def archive_current_scores(self):
        """
        Dipanggil oleh background worker setiap interval.
        1. Ambil semua tokens yang aktif (last_seen < 2h)
        2. Compute momentum + risk untuk masing-masing
        3. Insert ke momentum_snapshots dan risk_snapshots
        4. Deduplicate: skip jika snapshot identik dengan yang terakhir
        """
        pass
    
    async def get_historical_momentum(
        self,
        token_id: int,
        start: datetime,
        end: datetime
    ) -> list[MomentumSnapshot]:
        """Query snapshots untuk chart historis"""
        pass
    
    async def cleanup_old_snapshots(self, retention_days: int = 90):
        """Hapus snapshot lama sesuai retention policy"""
        pass
```

**Config changes:**

```python
# backend/src/pumpwatch/config.py
class Settings(BaseSettings):
    # ... existing fields
    archive_interval_minutes: int = 60  # Archive setiap 1 jam
    archive_retention_days: int = 90    # Simpan 90 hari
```

**Background worker integration:**

```python
# backend/src/pumpwatch/main.py
async def _background_archiver():
    interval = settings.archive_interval_minutes * 60
    archiver = DataArchiver(db)
    
    while True:
        await asyncio.sleep(interval)
        try:
            await archiver.archive_current_scores()
            logger.info("Snapshot archiving selesai")
        except Exception as e:
            logger.error(f"Archiving error: {e}")
```

#### API Endpoints

```python
# backend/src/pumpwatch/api/router.py (extend)
@router.get("/api/v1/tokens/{chain}/{address}/momentum-history")
async def get_momentum_history(
    chain: str,
    address: str,
    hours: int = 24
):
    """Return momentum score time-series"""
    pass

@router.get("/api/v1/tokens/{chain}/{address}/risk-history")
async def get_risk_history(
    chain: str,
    address: str,
    hours: int = 24
):
    """Return risk level changes over time"""
    pass
```

#### Frontend Integration

Update existing token detail page:
- Add historical momentum chart (line chart)
- Add historical risk flags timeline
- Show score/risk changes over selected period (1h, 4h, 24h, 7d)

---

### Feature 4: Advanced Alert System

**Tujuan:** Per-token threshold customization, per-pair cooldown, alert priority levels.

#### Database Schema Changes

```sql
-- User-defined alert rules (per token atau global)
CREATE TABLE alert_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    token_id INTEGER REFERENCES tokens(id) ON DELETE CASCADE,
    is_global BOOLEAN DEFAULT FALSE,
    momentum_threshold DECIMAL(5,2),
    risk_level_max VARCHAR(50),
    min_liquidity_usd DECIMAL(20,2),
    cooldown_minutes INTEGER DEFAULT 60,
    priority VARCHAR(20) DEFAULT 'normal',
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Cooldown tracking per pair
CREATE TABLE alert_cooldowns (
    id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES tokens(id) ON DELETE CASCADE,
    pool_id INTEGER REFERENCES pools(id) ON DELETE CASCADE,
    alert_rule_id INTEGER REFERENCES alert_rules(id) ON DELETE CASCADE,
    last_alert_sent_at TIMESTAMP NOT NULL,
    next_alert_allowed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(token_id, pool_id, alert_rule_id)
);

CREATE INDEX idx_alert_cooldowns_token_pool ON alert_cooldowns(token_id, pool_id);
CREATE INDEX idx_alert_cooldowns_next_allowed ON alert_cooldowns(next_alert_allowed_at);
```

#### Backend Implementation

**File:** `backend/src/pumpwatch/services/alert_manager.py`

```python
class AlertManager:
    async def create_alert_rule(self, rule: AlertRuleCreate) -> int:
        """Create custom alert rule"""
        pass
    
    async def check_alert_conditions(
        self,
        token_id: int,
        pool_id: int,
        score: MomentumScore,
        risk: RiskAssessment
    ) -> list[AlertRule]:
        """
        Return list of alert rules yang terpenuhi.
        Cek:
        1. Rule global + rule per-token
        2. Threshold momentum/risk
        3. Cooldown status
        """
        pass
    
    async def should_send_alert(
        self,
        token_id: int,
        pool_id: int,
        rule: AlertRule
    ) -> bool:
        """Check cooldown untuk token+pool+rule"""
        pass
    
    async def record_alert_sent(
        self,
        token_id: int,
        pool_id: int,
        rule: AlertRule
    ):
        """Update cooldown setelah alert terkirim"""
        pass
```

**File:** `backend/src/pumpwatch/api/alert_rules_router.py`

```python
@router.post("/api/v1/alert-rules")
async def create_alert_rule(rule: AlertRuleCreate):
    """Buat rule baru"""
    pass

@router.get("/api/v1/alert-rules")
async def list_alert_rules(token_id: int | None = None):
    """List rules (global atau per-token)"""
    pass

@router.patch("/api/v1/alert-rules/{rule_id}")
async def update_alert_rule(rule_id: int, updates: AlertRuleUpdate):
    """Update threshold/cooldown/enabled"""
    pass

@router.delete("/api/v1/alert-rules/{rule_id}")
async def delete_alert_rule(rule_id: int):
    """Hapus rule"""
    pass

@router.get("/api/v1/alert-rules/{rule_id}/cooldowns")
async def get_rule_cooldowns(rule_id: int):
    """List cooldowns aktif untuk rule tertentu"""
    pass
```

**Update ingestion service:**

```python
# backend/src/pumpwatch/services/ingestion.py
async def _maybe_create_signal(self, ...):
    # ... existing scoring logic
    
    # NEW: Check custom alert rules
    alert_manager = AlertManager(self.db)
    triggered_rules = await alert_manager.check_alert_conditions(
        token_id, pool_id, score, risk
    )
    
    for rule in triggered_rules:
        if await alert_manager.should_send_alert(token_id, pool_id, rule):
            await self._send_alert(token_id, pool_id, score, risk, rule)
            await alert_manager.record_alert_sent(token_id, pool_id, rule)
```

#### Frontend Implementation

**File:** `frontend/app/settings/alerts/page.tsx`

- List alert rules (table)
- Create/edit rule form:
  - Token selector (atau "Global rule")
  - Momentum threshold slider
  - Risk level dropdown
  - Min liquidity input
  - Cooldown minutes input
  - Priority select (low/normal/high)
  - Enable/disable toggle
- Active cooldowns view (per rule)

**File:** `frontend/app/tokens/[chain]/[address]/alerts.tsx`

Token-specific alert configuration panel (quick setup untuk single token).

---

## 4. Implementation Order

### Phase 1: Historical Archive (Foundation)
**Priority:** HIGH (dibutuhkan oleh backtest + analytics)

**Tasks:**
1. Database migrations untuk snapshot tables
2. Implement DataArchiver service
3. Integrate archiver ke background worker
4. Add retention cleanup job
5. API endpoints untuk historical data
6. Frontend charts update (momentum/risk history)

**Testing:**
- Archive frequency
- Deduplication logic
- Query performance untuk time-series
- Retention cleanup

**Estimasi:** 2-3 hari

---

### Phase 2: Advanced Alert System
**Priority:** HIGH (user-facing improvement)

**Tasks:**
1. Database migrations untuk alert_rules + cooldowns
2. Implement AlertManager service
3. Integrate ke ingestion flow
4. API endpoints untuk CRUD rules
5. Frontend settings page
6. Token-specific alert config

**Testing:**
- Cooldown enforcement
- Per-token vs global rules priority
- Rule evaluation performance
- Telegram formatting dengan priority

**Estimasi:** 2-3 hari

---

### Phase 3: Dashboard Analytics
**Priority:** MEDIUM (insights, bukan core functionality)

**Tasks:**
1. Database migrations untuk aggregates
2. Implement AnalyticsService
3. Background worker untuk periodic aggregation
4. API endpoints untuk trends + top tokens
5. Frontend analytics page dengan charts
6. Overview dashboard enhancement

**Testing:**
- Aggregation correctness
- Time-series query performance
- Chart rendering dengan large datasets

**Estimasi:** 3-4 hari

---

### Phase 4: Backtesting Engine
**Priority:** MEDIUM (validation tool, bukan production feature)

**Tasks:**
1. Database migrations untuk backtest tables
2. Implement BacktestEngine service
3. Exit strategy logic
4. Metrics calculation (sharpe, drawdown, dll)
5. API endpoints
6. Frontend backtest page
7. Equity curve + trades visualization

**Testing:**
- Historical signal replay
- Fee/slippage calculation accuracy
- Edge cases: missing data, delisted tokens
- Performance dengan large date ranges

**Estimasi:** 4-5 hari

---

## 5. Config Changes

```python
# backend/src/pumpwatch/config.py
class Settings(BaseSettings):
    # ... existing
    
    # Feature 3: Archive
    archive_interval_minutes: int = 60
    archive_retention_days: int = 90
    
    # Feature 2: Analytics
    analytics_aggregation_interval_minutes: int = 60
    
    # Feature 1: Backtest
    backtest_default_fee_percent: float = 0.01
    backtest_default_slippage_percent: float = 0.005
    backtest_max_concurrent_runs: int = 2
```

---

## 6. Migration Plan

```sql
-- Migration 002: Post-MVP Features
-- Run: psql -d pumpwatch -f backend/migrations/002_post_mvp_features.sql

BEGIN;

-- Feature 3: Historical Archive
CREATE TABLE momentum_snapshots (...);
CREATE TABLE risk_snapshots (...);
-- indexes

-- Feature 4: Advanced Alerts
CREATE TABLE alert_rules (...);
CREATE TABLE alert_cooldowns (...);
-- indexes

-- Feature 2: Analytics
CREATE TABLE momentum_aggregates (...);
CREATE TABLE risk_aggregates (...);
-- indexes

-- Feature 1: Backtest
CREATE TABLE backtest_runs (...);
CREATE TABLE backtest_trades (...);
-- indexes

COMMIT;
```

---

## 7. Security & Performance Considerations

### Security
- Alert rules API: protect dengan auth (jika multi-user)
- Backtest runs: limit concurrent runs per user
- Rate limit analytics endpoints
- Validate timeframe/date range inputs

### Performance
- Snapshot archival: batch insert, deduplicate in-memory first
- Analytics aggregation: use materialized view atau periodic job
- Historical queries: proper indexes + pagination
- Backtest: run async, store progress, allow cancellation

### Observability
- Log archive success/failure rates
- Monitor backtest queue depth
- Track analytics query latency
- Alert cooldown hit rate metrics

---

## 8. Testing Strategy

### Unit Tests
- AlertManager cooldown logic
- BacktestEngine metrics calculation
- AnalyticsService aggregation
- DataArchiver deduplication

### Integration Tests
- End-to-end backtest run
- Alert rule evaluation + Telegram send
- Historical data query performance
- Analytics aggregation correctness

### Manual Testing
- Frontend charts responsiveness
- Backtest result interpretation
- Alert rule UX flow
- Analytics dashboard usability

---

## 9. Documentation Updates

Update README.md dengan:
- Fitur baru (4 sections)
- Config vars baru
- API endpoints baru
- Migration commands

Update AGENTS.md dengan:
- Backtest evaluation guidelines
- Alert rule best practices
- Historical data retention policy

---

## 10. Rollout Plan

1. Deploy migration 002
2. Deploy backend dengan feature flags (disabled by default)
3. Run archiver manually untuk test
4. Enable archiver background worker
5. Deploy frontend
6. Enable alert rules (global default first)
7. Enable analytics aggregation
8. Enable backtest (admin only first)
9. Monitor metrics untuk 24h
10. Enable untuk all users

---

## 11. Success Metrics

### Feature 1: Backtest
- Users dapat run backtest dalam < 30 detik untuk 7 hari data
- Metrics akurat vs manual calculation
- At least 3 backtest runs created dalam minggu pertama

### Feature 2: Analytics
- Dashboard load < 2 detik
- Aggregation lag < 5 menit dari real-time
- Users mengakses analytics page (track usage)

### Feature 3: Archive
- Zero data loss dalam archival
- Query latency < 500ms untuk 24h data
- Storage growth predictable

### Feature 4: Advanced Alerts
- Per-token cooldown respected 100%
- Alert spam reduction (measure alerts/hour before vs after)
- At least 5 custom rules created dalam minggu pertama

---

## 12. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Archive storage growth | Database bloat | Retention policy + monitoring |
| Backtest slow for large ranges | Poor UX | Async + progress tracking |
| Analytics aggregation lag | Stale data | Increase frequency + cache |
| Complex alert rules konflik | Alert spam | Priority system + testing |
| Historical data gaps | Backtest inaccurate | Forward-fill + coverage indicator |

---

## 13. Future Enhancements (Out of Scope)

- Multi-chain backtest comparison
- Custom exit strategy builder (UI)
- Alert rules marketplace (share configs)
- ML model training dari archived data
- Real-time analytics streaming
- Export backtest results (CSV/PDF)

---

**Status:** Draft selesai, siap untuk task breakdown.
**Next step:** Load skill `create-issues` untuk generate atomic tasks.
