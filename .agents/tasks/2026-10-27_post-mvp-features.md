# Tasks: Post-MVP Features

**Dokumen:** Task breakdown untuk 4 fitur post-MVP\
**Tanggal:** 2026-10-27\
**Tech Spec:** `.agents/tech-specs/2026/post-mvp-features.md`\
**Status:** Ready for implementation

---

## Phase 1: Historical Data Archive (Foundation)

### T-01: Database migration untuk snapshot tables
- **Modul:** Database
- **Prioritas:** High
- **Status:** Todo
- **Dependensi:** -
- **Estimasi:** 1 jam
- **Deskripsi:**
  - Buat migration file `002_post_mvp_features.sql`
  - Tambah table `momentum_snapshots` (id, token_id, pool_id, snapshot_at, momentum_score, score_components, features, data_coverage, rules_version, created_at)
  - Tambah table `risk_snapshots` (id, token_id, pool_id, snapshot_at, risk_level, hard_block, flags, coverage, rules_version, created_at)
  - Tambah indexes: token_id + snapshot_at DESC, snapshot_at DESC
- **File:**
  - `backend/migrations/002_post_mvp_features.sql`
- **Testing:**
  - Run migration di database lokal
  - Verify tables + indexes created

---

### T-02: Implement DataArchiver service
- **Modul:** Backend Service
- **Prioritas:** High
- **Status:** Todo
- **Dependensi:** T-01
- **Estimasi:** 3 jam
- **Deskripsi:**
  - Buat `backend/src/pumpwatch/services/archiver.py`
  - Class `DataArchiver` dengan methods:
    - `archive_current_scores()` - ambil active tokens, compute score/risk, insert snapshot
    - `get_historical_momentum(token_id, start, end)` - query momentum snapshots
    - `get_historical_risk(token_id, start, end)` - query risk snapshots
    - `cleanup_old_snapshots(retention_days)` - hapus data lama
  - Deduplication: skip jika score/risk sama dengan snapshot terakhir
  - Batch insert untuk performance
- **File:**
  - `backend/src/pumpwatch/services/archiver.py`
- **Testing:**
  - Unit test: deduplication logic
  - Unit test: batch insert
  - Integration test: archive + query snapshots

---

### T-03: Add config untuk archiver
- **Modul:** Backend Config
- **Prioritas:** High
- **Status:** Todo
- **Dependensi:** T-02
- **Estimasi:** 30 menit
- **Deskripsi:**
  - Update `backend/src/pumpwatch/config.py`
  - Tambah fields: `archive_interval_minutes` (default 60), `archive_retention_days` (default 90)
  - Update `.env.example` dengan dokumentasi
- **File:**
  - `backend/src/pumpwatch/config.py`
  - `backend/.env.example`
- **Testing:**
  - Verify config loaded correctly

---

### T-04: Integrate archiver ke background worker
- **Modul:** Backend Worker
- **Prioritas:** High
- **Status:** Todo
- **Dependensi:** T-02, T-03
- **Estimasi:** 2 jam
- **Deskripsi:**
  - Update `backend/src/pumpwatch/main.py`
  - Buat async task `_background_archiver()` yang loop setiap `archive_interval_minutes`
  - Panggil `archiver.archive_current_scores()` setiap interval
  - Error handling + logging
  - Start/stop di lifespan context manager
- **File:**
  - `backend/src/pumpwatch/main.py`
- **Testing:**
  - Manual test: run server, verify archiver berjalan
  - Check logs untuk archive success
  - Verify snapshots tersimpan di DB

---

### T-05: API endpoints untuk historical data
- **Modul:** Backend API
- **Prioritas:** High
- **Status:** Todo
- **Dependensi:** T-02
- **Estimasi:** 2 jam
- **Deskripsi:**
  - Update `backend/src/pumpwatch/api/router.py`
  - Tambah endpoints:
    - `GET /api/v1/tokens/{chain}/{address}/momentum-history?hours=24` - momentum time-series
    - `GET /api/v1/tokens/{chain}/{address}/risk-history?hours=24` - risk time-series
  - Return format: list of {snapshot_at, score/risk_level, components/flags}
  - Pagination untuk large ranges
- **File:**
  - `backend/src/pumpwatch/api/router.py`
- **Testing:**
  - Integration test: call endpoints, verify response
  - Test dengan missing data
  - Test pagination

---

### T-06: Frontend historical charts
- **Modul:** Frontend
- **Prioritas:** Medium
- **Status:** Todo
- **Dependensi:** T-05
- **Estimasi:** 3 jam
- **Deskripsi:**
  - Update `frontend/app/page.tsx` (token detail view)
  - Tambah section "Historical Trends"
  - Line chart untuk momentum score over time (Recharts)
  - Timeline untuk risk level changes
  - Timeframe selector: 1h, 4h, 24h, 7d
  - Loading/error states
- **File:**
  - `frontend/app/page.tsx`
- **Testing:**
  - Manual test: verify charts render correctly
  - Test dengan data kosong
  - Test responsive layout

---

## Phase 2: Advanced Alert System

### T-07: Database migration untuk alert rules + cooldowns
- **Modul:** Database
- **Prioritas:** High
- **Status:** Todo
- **Dependensi:** T-01
- **Estimasi:** 1 jam
- **Deskripsi:**
  - Update migration `002_post_mvp_features.sql`
  - Tambah table `alert_rules` (id, name, token_id, is_global, momentum_threshold, risk_level_max, min_liquidity_usd, cooldown_minutes, priority, enabled, created_at, updated_at)
  - Tambah table `alert_cooldowns` (id, token_id, pool_id, alert_rule_id, last_alert_sent_at, next_alert_allowed_at, created_at)
  - Unique constraint: (token_id, pool_id, alert_rule_id)
  - Indexes: token_id+pool_id, next_alert_allowed_at
- **File:**
  - `backend/migrations/002_post_mvp_features.sql`
- **Testing:**
  - Run migration
  - Verify constraints + indexes

---

### T-08: Implement AlertManager service
- **Modul:** Backend Service
- **Prioritas:** High
- **Status:** Todo
- **Dependensi:** T-07
- **Estimasi:** 4 jam
- **Deskripsi:**
  - Buat `backend/src/pumpwatch/services/alert_manager.py`
  - Class `AlertManager` dengan methods:
    - `create_alert_rule(rule)` - insert rule
    - `check_alert_conditions(token_id, pool_id, score, risk)` - return triggered rules
    - `should_send_alert(token_id, pool_id, rule)` - check cooldown
    - `record_alert_sent(token_id, pool_id, rule)` - update cooldown
  - Logic: per-token rules override global rules
  - Priority sorting: high > normal > low
- **File:**
  - `backend/src/pumpwatch/services/alert_manager.py`
  - `backend/src/pumpwatch/domain/alerts.py` (domain models)
- **Testing:**
  - Unit test: cooldown logic
  - Unit test: rule matching (global vs per-token)
  - Unit test: priority sorting
  - Integration test: DB operations

---

### T-09: Integrate alert manager ke ingestion
- **Modul:** Backend Service
- **Prioritas:** High
- **Status:** Todo
- **Dependensi:** T-08
- **Estimasi:** 2 jam
- **Deskripsi:**
  - Update `backend/src/pumpwatch/services/ingestion.py`
  - Di `_maybe_create_signal()`, panggil `alert_manager.check_alert_conditions()`
  - Loop triggered rules, check cooldown, send alert, record sent
  - Update Telegram alert format untuk include priority
- **File:**
  - `backend/src/pumpwatch/services/ingestion.py`
- **Testing:**
  - Integration test: signal triggers alert with custom rule
  - Test cooldown respected
  - Test multiple rules per token

---

### T-10: API endpoints untuk alert rules CRUD
- **Modul:** Backend API
- **Prioritas:** High
- **Status:** Todo
- **Dependensi:** T-08
- **Estimasi:** 3 jam
- **Deskripsi:**
  - Buat `backend/src/pumpwatch/api/alert_rules_router.py`
  - Endpoints:
    - `POST /api/v1/alert-rules` - create rule
    - `GET /api/v1/alert-rules?token_id={id}` - list rules
    - `PATCH /api/v1/alert-rules/{rule_id}` - update rule
    - `DELETE /api/v1/alert-rules/{rule_id}` - delete rule
    - `GET /api/v1/alert-rules/{rule_id}/cooldowns` - list active cooldowns
  - Validation: threshold range, cooldown min/max
  - Include router di `main.py`
- **File:**
  - `backend/src/pumpwatch/api/alert_rules_router.py`
  - `backend/src/pumpwatch/main.py`
- **Testing:**
  - Integration test: CRUD operations
  - Test validation errors
  - Test pagination

---

### T-11: Frontend alert rules settings page
- **Modul:** Frontend
- **Prioritas:** High
- **Status:** Todo
- **Dependensi:** T-10
- **Estimasi:** 4 jam
- **Deskripsi:**
  - Buat `frontend/app/settings/alerts/page.tsx`
  - Sections:
    - Rules table (name, threshold, cooldown, enabled, actions)
    - Create rule form (modal atau separate page)
    - Edit rule form (inline atau modal)
    - Delete confirmation
    - Active cooldowns view (per rule)
  - Form fields: token selector (atau "Global"), momentum threshold slider, risk level dropdown, min liquidity, cooldown minutes, priority select, enabled toggle
  - Navigation link dari settings page
- **File:**
  - `frontend/app/settings/alerts/page.tsx`
- **Testing:**
  - Manual test: CRUD operations
  - Test form validation
  - Test responsive layout

---

### T-12: Frontend token-specific alert config
- **Modul:** Frontend
- **Prioritas:** Medium
- **Status:** Todo
- **Dependensi:** T-10
- **Estimasi:** 2 jam
- **Deskripsi:**
  - Update token detail page (`frontend/app/page.tsx`)
  - Tambah "Alert Settings" panel (collapsible)
  - Quick setup: create rule untuk token ini dengan form sederhana
  - Show existing rules untuk token ini
  - Link ke full settings page
- **File:**
  - `frontend/app/page.tsx`
- **Testing:**
  - Manual test: create rule dari token detail
  - Verify rule muncul di settings page

---

## Phase 3: Dashboard Analytics

### T-13: Database migration untuk aggregates
- **Modul:** Database
- **Prioritas:** Medium
- **Status:** Todo
- **Dependensi:** T-01
- **Estimasi:** 1 jam
- **Deskripsi:**
  - Update migration `002_post_mvp_features.sql`
  - Tambah table `momentum_aggregates` (id, time_bucket, timeframe, avg_momentum_score, median_momentum_score, high_momentum_count, medium_momentum_count, low_momentum_count, avg_liquidity_usd, total_tokens_scanned, created_at)
  - Tambah table `risk_aggregates` (id, time_bucket, timeframe, low_risk_count, medium_risk_count, high_risk_count, hard_blocked_count, avg_risk_coverage, created_at)
  - Unique constraint: (time_bucket, timeframe)
  - Indexes: time_bucket DESC
- **File:**
  - `backend/migrations/002_post_mvp_features.sql`
- **Testing:**
  - Run migration
  - Verify constraints + indexes

---

### T-14: Implement AnalyticsService
- **Modul:** Backend Service
- **Prioritas:** Medium
- **Status:** Todo
- **Dependensi:** T-13
- **Estimasi:** 4 jam
- **Deskripsi:**
  - Buat `backend/src/pumpwatch/services/analytics.py`
  - Class `AnalyticsService` dengan methods:
    - `compute_aggregates(timeframe)` - hitung agregat untuk window terakhir (1h/4h/24h)
    - `get_momentum_trend(timeframe, hours)` - query time-series aggregates
    - `get_risk_trend(timeframe, hours)` - query risk distribution trend
    - `get_top_tokens(category, limit)` - query top tokens per kategori (high_momentum, watchlist, high_liquidity, new_pools)
    - `get_overview()` - dashboard summary stats
  - Aggregation logic: avg/median/count dari market_snapshots + signals
- **File:**
  - `backend/src/pumpwatch/services/analytics.py`
- **Testing:**
  - Unit test: aggregation calculations
  - Integration test: compute + query aggregates
  - Test edge cases: no data, single data point

---

### T-15: Integrate analytics ke background worker
- **Modul:** Backend Worker
- **Prioritas:** Medium
- **Status:** Todo
- **Dependensi:** T-14
- **Estimasi:** 1 jam
- **Deskripsi:**
  - Update `backend/src/pumpwatch/main.py`
  - Buat async task `_background_analytics()` yang loop setiap `analytics_aggregation_interval_minutes`
  - Panggil `analytics.compute_aggregates()` untuk 1h, 4h, 24h
  - Error handling + logging
  - Start/stop di lifespan
- **File:**
  - `backend/src/pumpwatch/main.py`
  - `backend/src/pumpwatch/config.py` (tambah `analytics_aggregation_interval_minutes`)
- **Testing:**
  - Manual test: verify aggregation berjalan
  - Check logs + DB records

---

### T-16: API endpoints untuk analytics
- **Modul:** Backend API
- **Prioritas:** Medium
- **Status:** Todo
- **Dependensi:** T-14
- **Estimasi:** 2 jam
- **Deskripsi:**
  - Buat `backend/src/pumpwatch/api/analytics_router.py`
  - Endpoints:
    - `GET /api/v1/analytics/momentum/trend?timeframe=1h&hours=24` - momentum trend
    - `GET /api/v1/analytics/risk/trend?timeframe=1h&hours=24` - risk distribution trend
    - `GET /api/v1/analytics/top-tokens?category=high_momentum&limit=10` - top tokens
    - `GET /api/v1/analytics/overview` - dashboard overview
  - Include router di `main.py`
- **File:**
  - `backend/src/pumpwatch/api/analytics_router.py`
  - `backend/src/pumpwatch/main.py`
- **Testing:**
  - Integration test: call endpoints
  - Test query performance
  - Test missing data scenarios

---

### T-17: Frontend analytics page
- **Modul:** Frontend
- **Prioritas:** Medium
- **Status:** Todo
- **Dependensi:** T-16
- **Estimasi:** 5 jam
- **Deskripsi:**
  - Buat `frontend/app/analytics/page.tsx`
  - Sections:
    1. Overview cards (24h stats: total scanned, avg momentum, risk distribution)
    2. Momentum trend chart (line chart, timeframe selector)
    3. Risk distribution chart (stacked bar atau area chart)
    4. Top tokens table (tabs: high momentum, watchlist, high liquidity, new pools)
    5. Momentum vs Risk scatter plot (heatmap)
  - Loading/error states
  - Responsive layout
  - Add navigation link
- **File:**
  - `frontend/app/analytics/page.tsx`
  - `frontend/app/layout.tsx` (add nav link)
- **Testing:**
  - Manual test: verify charts render
  - Test dengan missing data
  - Test responsive layout
  - Test timeframe switching

---

## Phase 4: Backtesting Engine

### T-18: Database migration untuk backtest tables
- **Modul:** Database
- **Prioritas:** Medium
- **Status:** Todo
- **Dependensi:** T-01
- **Estimasi:** 1 jam
- **Deskripsi:**
  - Update migration `002_post_mvp_features.sql`
  - Tambah table `backtest_runs` (id, name, strategy_config, fee_percent, slippage_percent, start_date, end_date, status, created_at, completed_at, summary_stats)
  - Tambah table `backtest_trades` (id, backtest_run_id, signal_id, token_id, entry_timestamp, entry_price, exit_timestamp, exit_price, position_size_usd, gross_return, net_return, fees_paid, slippage_impact, exit_reason, created_at)
  - Indexes: backtest_run_id, signal_id
- **File:**
  - `backend/migrations/002_post_mvp_features.sql`
- **Testing:**
  - Run migration
  - Verify foreign keys + indexes

---

### T-19: Implement BacktestEngine service
- **Modul:** Backend Service
- **Prioritas:** Medium
- **Status:** Todo
- **Dependensi:** T-18
- **Estimasi:** 6 jam
- **Deskripsi:**
  - Buat `backend/src/pumpwatch/services/backtest.py`
  - Class `BacktestEngine` dengan methods:
    - `run_backtest(start_date, end_date, strategy_params)` - main backtest loop
    - `simulate_trade(signal, exit_rules)` - simulate entry + exit untuk 1 signal
    - `calculate_exit_price(entry_price, exit_reason, slippage)` - apply slippage
    - `calculate_metrics(trades)` - aggregate metrics (win_rate, avg_return, sharpe, max_drawdown, total_fees)
  - Exit rules: time-based (1h/4h/24h), profit target (+20%/+50%/+100%), stop-loss (-15%), trailing stop (-10% dari peak)
  - Query market_snapshots untuk historical prices
  - Handle missing data: skip trade jika tidak ada exit price
- **File:**
  - `backend/src/pumpwatch/services/backtest.py`
  - `backend/src/pumpwatch/domain/backtest.py` (domain models)
- **Testing:**
  - Unit test: exit rules logic
  - Unit test: fee/slippage calculation
  - Unit test: metrics calculation (sharpe, drawdown)
  - Integration test: full backtest run dengan fixture data
  - Test edge cases: delisted token, missing snapshots

---

### T-20: Add backtest config
- **Modul:** Backend Config
- **Prioritas:** Medium
- **Status:** Todo
- **Dependensi:** T-19
- **Estimasi:** 30 menit
- **Deskripsi:**
  - Update `backend/src/pumpwatch/config.py`
  - Tambah fields: `backtest_default_fee_percent` (0.01), `backtest_default_slippage_percent` (0.005), `backtest_max_concurrent_runs` (2)
  - Update `.env.example`
- **File:**
  - `backend/src/pumpwatch/config.py`
  - `backend/.env.example`
- **Testing:**
  - Verify config loaded

---

### T-21: API endpoints untuk backtest
- **Modul:** Backend API
- **Prioritas:** Medium
- **Status:** Todo
- **Dependensi:** T-19, T-20
- **Estimasi:** 3 jam
- **Deskripsi:**
  - Buat `backend/src/pumpwatch/api/backtest_router.py`
  - Endpoints:
    - `POST /api/v1/backtest/run` - create + run backtest (async, return run_id immediately)
    - `GET /api/v1/backtest/runs?limit=20&offset=0` - list runs
    - `GET /api/v1/backtest/runs/{run_id}` - get result + metrics
    - `GET /api/v1/backtest/runs/{run_id}/trades?limit=50` - list trades
  - Validation: date range max 90 days, concurrent runs limit
  - Run backtest di background task (asyncio.create_task)
  - Include router di `main.py`
- **File:**
  - `backend/src/pumpwatch/api/backtest_router.py`
  - `backend/src/pumpwatch/main.py`
- **Testing:**
  - Integration test: create backtest, wait for completion, verify results
  - Test validation errors
  - Test concurrent runs limit

---

### T-22: Frontend backtest page
- **Modul:** Frontend
- **Prioritas:** Medium
- **Status:** Todo
- **Dependensi:** T-21
- **Estimasi:** 5 jam
- **Deskripsi:**
  - Buat `frontend/app/backtest/page.tsx`
  - Sections:
    1. Create backtest form (date range pickers, strategy params, fee/slippage inputs, submit button)
    2. Runs list table (name, date range, status, metrics summary, actions)
    3. Detail view (modal atau separate route):
       - Metrics cards (total trades, win rate, avg return, sharpe, max drawdown, fees, slippage)
       - Equity curve chart (line chart)
       - Drawdown chart (area chart)
       - Trades table (entry/exit time, price, return, reason)
  - Polling untuk status updates (pending -> running -> completed)
  - Loading/error states
  - Add navigation link
- **File:**
  - `frontend/app/backtest/page.tsx`
  - `frontend/app/layout.tsx` (add nav link)
- **Testing:**
  - Manual test: create backtest, verify completion
  - Test charts render correctly
  - Test responsive layout
  - Test polling logic

---

## Documentation & Finalization

### T-23: Update README.md
- **Modul:** Documentation
- **Prioritas:** Low
- **Status:** Todo
- **Dependensi:** T-22
- **Estimasi:** 1 jam
- **Deskripsi:**
  - Update README.md dengan:
    - 4 fitur baru (sections)
    - Config vars baru (archive_interval_minutes, analytics_aggregation_interval_minutes, backtest_default_fee_percent, backtest_default_slippage_percent)
    - API endpoints baru (list + deskripsi)
    - Migration command untuk 002
  - Update "Fitur MVP" section ke "Fitur"
- **File:**
  - `README.md`
- **Testing:**
  - Review documentation clarity

---

### T-24: Update AGENTS.md
- **Modul:** Documentation
- **Prioritas:** Low
- **Status:** Todo
- **Dependensi:** T-23
- **Estimasi:** 30 menit
- **Deskripsi:**
  - Update AGENTS.md dengan:
    - Backtest evaluation guidelines (avoid overfitting, out-of-sample, include failed signals)
    - Alert rule best practices (global vs per-token, cooldown tuning)
    - Historical data retention policy (default 90 days)
- **File:**
  - `AGENTS.md`
- **Testing:**
  - Review guidelines completeness

---

### T-25: End-to-end testing
- **Modul:** Testing
- **Prioritas:** High
- **Status:** Todo
- **Dependensi:** T-06, T-12, T-17, T-22
- **Estimasi:** 4 jam
- **Deskripsi:**
  - Manual E2E testing untuk semua fitur:
    - Archiver: verify snapshots tersimpan setiap interval, query historical data
    - Alert rules: create rule, trigger alert, verify cooldown respected
    - Analytics: verify aggregates accurate, charts render, top tokens correct
    - Backtest: run backtest untuk 7 hari, verify metrics accurate, equity curve matches trades
  - Performance testing: archiver dengan 100+ tokens, analytics query dengan 1000+ records, backtest dengan 50+ signals
  - Error scenarios: missing data, API errors, concurrent operations
  - Document test results + known issues
- **File:**
  - `.agents/test-results/post-mvp-features.md` (new file)
- **Testing:**
  - Checklist semua fitur tested

---

### T-26: Deployment prep
- **Modul:** Deployment
- **Prioritas:** High
- **Status:** Todo
- **Dependensi:** T-25
- **Estimasi:** 2 jam
- **Deskripsi:**
  - Rollout plan:
    1. Backup database
    2. Deploy migration 002
    3. Deploy backend dengan feature flags (ARCHIVE_ENABLED=false, ANALYTICS_ENABLED=false, BACKTEST_ENABLED=false)
    4. Run archiver manually untuk smoke test
    5. Enable ARCHIVE_ENABLED=true, monitor logs untuk 1 jam
    6. Deploy frontend
    7. Enable alert rules (create 1 global default rule)
    8. Enable ANALYTICS_ENABLED=true, monitor aggregation
    9. Enable BACKTEST_ENABLED=true (admin only first via config)
    10. Monitor metrics untuk 24h
    11. Enable backtest untuk all users
  - Create rollback script (drop tables, revert code)
  - Update `.env.example` dengan feature flags
- **File:**
  - `backend/.env.example`
  - `DEPLOYMENT.md` (new file with rollout steps)
- **Testing:**
  - Dry-run deployment steps di local

---

## Summary

**Total tasks:** 26\
**Estimasi total:** ~60 jam (~8 hari kerja untuk 1 developer)

**Phase priority:**
1. **Phase 1 (Archive):** T-01 sampai T-06 - foundation untuk fitur lain
2. **Phase 2 (Advanced Alerts):** T-07 sampai T-12 - user-facing improvement
3. **Phase 3 (Analytics):** T-13 sampai T-17 - insights
4. **Phase 4 (Backtest):** T-18 sampai T-22 - validation tool
5. **Finalization:** T-23 sampai T-26 - docs + deployment

**Critical path:** T-01 → T-02 → T-04 → T-05 → T-06 (Archive) → T-25 (E2E testing) → T-26 (Deploy)

**Parallel work opportunities:**
- Phase 2 (Alerts) dapat dimulai setelah T-01 (tidak depend on archiver implementation)
- Phase 3 (Analytics) dapat dimulai setelah T-01
- Phase 4 (Backtest) dapat dimulai setelah T-01, tapi lebih baik setelah T-06 (archive selesai) untuk data historis yang lengkap

**Next step:** Mulai implementasi dari T-01 (database migration).
