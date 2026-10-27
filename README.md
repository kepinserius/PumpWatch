# PumpWatch --- Memecoin Momentum & Risk Scanner

PumpWatch adalah scanner memecoin yang membantu mengidentifikasi perubahan aktivitas pasar dan memaparkan risiko token secara transparan. Sistem tidak menjamin kenaikan harga dan tidak mengeksekusi transaksi.

## Fitur

### Core Features
- **Solana-only** read-only scanner dengan DexScreener integration
- **Risk engine** dengan liquidity checks, data quality validation
- **Momentum scoring** rule-based 6 komponen (0-100)
- **Dashboard** Next.js dengan watchlist & price charts
- **Telegram alerts** dengan cooldown & deduplication

### Post-MVP Features
- **Historical Data Archive** - snapshot momentum/risk setiap interval (default 60 menit), retention 90 hari
- **Advanced Alert System** - per-token & global alert rules dengan cooldown tracking per pair
- **Dashboard Analytics** - trend momentum/risk per timeframe (1h/4h/24h), top tokens per kategori
- **Backtesting Engine** - rule-based strategy testing dengan fee/slippage calculation & equity curve

### Testing & Observability
- **Comprehensive tests** - unit, integration, E2E testing untuk semua fitur
- **Background workers** - scanner, archiver, analytics aggregation (run 24/7)

## Tech Stack

**Backend:**
- Python 3.12+ + FastAPI
- PostgreSQL untuk storage
- asyncpg untuk async database
- httpx untuk API calls
- pytest + pytest-asyncio untuk testing

**Frontend:**
- Next.js 15 + TypeScript
- TanStack Query untuk data fetching
- Recharts untuk charts
- Tailwind CSS

## Setup

### Prerequisites

```bash
# Install Python 3.12+
python3 --version

# Install PostgreSQL
sudo dnf install postgresql postgresql-server  # Fedora/RHEL
# atau: sudo apt install postgresql postgresql-client  # Debian/Ubuntu

# Install Node.js 20+
node --version
npm --version
```

### Database Setup

```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Create database
createdb pumpwatch

# Run migrations (semua)
psql -d pumpwatch -f backend/migrations/001_initial_schema.sql
psql -d pumpwatch -f backend/migrations/003_post_mvp_features.sql
```

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env

# Edit .env dengan konfigurasi Anda
nano .env
```

**Required environment variables:**

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pumpwatch
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
MIN_LIQUIDITY_USD=5000.0
MOMENTUM_THRESHOLD=65

# Post-MVP features
ARCHIVE_INTERVAL_MINUTES=60
ARCHIVE_RETENTION_DAYS=90
ANALYTICS_AGGREGATION_INTERVAL_MINUTES=60
```

**Optional config for Post-MVP:**
```env
# Alert system
ADMIN_API_KEY=your_admin_key  # untuk admin endpoints

# Backtest defaults
BACKTEST_DEFAULT_FEE_PERCENT=0.01
BACKTEST_DEFAULT_SLIPPAGE_PERCENT=0.005
```

**Cara mendapat Telegram Bot Token:**
1. Chat dengan [@BotFather](https://t.me/BotFather) di Telegram
2. Kirim `/newbot` dan ikuti instruksi
3. Copy token yang diberikan
4. Untuk chat_id: kirim pesan ke bot Anda, lalu akses `https://api.telegram.org/bot<TOKEN>/getUpdates`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Development mode
npm run dev

# Production mode
npm run build && npm start
```

## Running

### Backend

```bash
cd backend
source .venv/bin/activate

# Run API server
uvicorn pumpwatch.main:app --reload --host 0.0.0.0 --port 8000
```

API tersedia di `http://localhost:8000`  
API Docs: `http://localhost:8000/docs`

**Background workers yang otomatis jalan:**
- Scanner: scan token setiap 5 menit (configurable via `SCAN_INTERVAL_MINUTES`)
- Archiver: archive momentum/risk setiap 60 menit (configurable via `ARCHIVE_INTERVAL_MINUTES`)
- Analytics: compute aggregates setiap 60 menit (configurable via `ANALYTICS_AGGREGATION_INTERVAL_MINUTES`)

### Frontend

```bash
cd frontend

# Development mode
npm run dev

# Production mode
npm run build && npm start
```

Frontend tersedia di `http://localhost:3000`

## Testing

```bash
cd backend
source .venv/bin/activate

# Run all tests
pytest -v

# Run specific test file
pytest tests/test_health.py -v
pytest tests/test_alerts.py -v

# Run with coverage
pytest --cov=pumpwatch tests/
```

## API Endpoints

### Health & Status
- `GET /health` — liveness check
- `GET /ready` — readiness check (database + workers status)

### Providers
- `GET /api/v1/providers/health` — DexScreener status

### Tokens
- `GET /api/v1/tokens` — list tokens (pagination)
- `GET /api/v1/tokens/{chain}/{address}` — token detail
- `GET /api/v1/tokens/{chain}/{address}/score` — risk + momentum score
- `GET /api/v1/tokens/{chain}/{address}/snapshots` — market history
- `GET /api/v1/tokens/{chain}/{address}/momentum-history?hours=24` — historical momentum snapshots
- `GET /api/v1/tokens/{chain}/{address}/risk-history?hours=24` — historical risk snapshots

### Signals
- `GET /api/v1/signals` — list signals (pagination)
- `GET /api/v1/signals/{id}` — signal detail

### Analytics (Post-MVP)
- `GET /api/v1/analytics/momentum/trend?timeframe=1h&hours=24` — momentum trend time-series
- `GET /api/v1/analytics/risk/trend?timeframe=1h&hours=24` — risk distribution trend
- `GET /api/v1/analytics/top-tokens?category=high_momentum&limit=10` — top tokens per kategori
- `GET /api/v1/analytics/overview` — dashboard overview stats

### Alert Rules (Post-MVP)
- `POST /api/v1/alert-rules` — create alert rule
- `GET /api/v1/alert-rules` — list alert rules
- `GET /api/v1/alert-rules/{rule_id}` — get single rule
- `PATCH /api/v1/alert-rules/{rule_id}` — update rule
- `DELETE /api/v1/alert-rules/{rule_id}` — delete rule
- `GET /api/v1/alert-rules/{rule_id}/cooldowns` — list active cooldowns per rule

### Backtesting (Post-MVP)
- `POST /api/v1/backtest/run` — create & run backtest
- `GET /api/v1/backtest/runs` — list backtest runs
- `GET /api/v1/backtest/runs/{run_id}` — get backtest results + metrics
- `GET /api/v1/backtest/runs/{run_id}/trades` — list trades dari backtest

### Admin
- `POST /api/v1/admin/scan?chain=solana` — trigger manual scan
- `POST /api/v1/admin/rescore?chain=solana` — re-score semua tokens
- `POST /api/v1/admin/cleanup-snapshots?retention_days=90` — cleanup old snapshots (admin only)

## Architecture

```
External Market Data APIs (DexScreener)
            ↓
    Provider Adapter → Validation → PostgreSQL (snapshots)
                                          ↓
                                   +-------+-------+
                                   |       |       |
                                   v       v       v
                            DataArchiver  Analytics  Ingestion
                                   |       |       |
                                   v       v       v
                            momentum_snapshots  risk_snapshots
                                              ↓
                                    Momentum Engine + Risk Engine
                                              ↓
                                      Signal Evaluator
                                              ↓
                               +--------------+--------------+
                               |              |              |
                               v              v              v
                        Telegram Alerts  FastAPI (Dashboard)  Backtest Engine
                               |              |              |
                               v              v              v
                           Alerts DB     Frontend        backtest_runs
                                                      +
                                                      v
                                               backtest_trades
```

## Prinsip

1. **Risk-first**: Hard-block risk mengalahkan momentum score
2. **Explainable**: Semua skor dapat diaudit dengan komponen dan coverage
3. **No false certainty**: Skor bukan probabilitas pump, bukan jaminan profit
4. **Data provenance**: Tampilkan sumber, waktu, dan status data
5. **Fail safely**: Data missing/stale = unknown, bukan aman atau 0
6. **Backtest-first**: Validasi strategi historis sebelum live execution

## Post-MVP Features Detail

### Historical Data Archive
- **Tables**: `momentum_snapshots`, `risk_snapshots`
- **Interval**: Default 60 menit (config via `ARCHIVE_INTERVAL_MINUTES`)
- **Retention**: Default 90 hari (config via `ARCHIVE_RETENTION_DAYS`)
- **Deduplication**: Skip jika score/risk sama dengan snapshot terakhir
- **Query**: Historical momentum/risk charts per token

### Advanced Alert System
- **Global rules**: Berlaku untuk semua token
- **Per-token rules**: Override global rules untuk token tertentu
- **Cooldown**: Per-token + per-pair + per-rule tracking
- **Priority**: high/normal/low - high priority alerts lebih cepat
- **Rules**: momentum threshold, risk level max, min liquidity

### Dashboard Analytics
- **Aggregates**: Momentum & risk per timeframe (1h/4h/24h)
- **Trends**: Time-series charts untuk momentum/risk distribution
- **Top tokens**: High momentum, Watchlist, High liquidity, New pools
- **Overview**: Total tokens, scanned 24h, avg momentum, risk distribution

### Backtesting Engine
- **Strategy**: Time-based exit (1h/4h/24h), profit targets, stop-loss
- **Fee/slippage**: Configurable (default: 1% fee, 0.5% slippage)
- **Metrics**: Win rate, avg return, max return, min return, equity curve
- **Exit reason**: time_based, profit_target, stop_loss

## Dokumentasi Lengkap

- `PRD.md` — Product requirements, scope, architecture
- `AGENTS.md` — AI coding agent instructions
- `backend/migrations/README.md` — Database migration guide
- `.agents/tech-specs/2026/post-mvp-features.md` — Tech spec untuk post-MVP features
- `.agents/tasks/2026-10-27_post-mvp-features.md` — Task breakdown

## Troubleshooting

**Database connection error:**
```bash
# Check PostgreSQL running
sudo systemctl status postgresql

# Check database exists
psql -l | grep pumpwatch

# Test connection
psql -d pumpwatch -c "SELECT 1"
```

**Background worker not running:**
```bash
# Check backend logs
tail -f backend/logs/*.log

# Verify worker is started (check /ready endpoint)
curl http://localhost:8000/ready
# Should show: "scanner": "running", "archiver": "running", "archiver": "running"
```

**Alert rules not triggering:**
- Verify `ALERT_COOLDOWN_MINUTES` di `.env`
- Check alert rules enabled & conditions match current data
- Review logs untuk rule evaluation details

**No backtest results:**
- Verify signals exist dalam date range
- Check fee/slippage config (too high values can cause all losing trades)
- Check backend logs untuk signal simulation errors

**Frontend can't connect to backend:**
- Pastikan backend running di port 8000
- Check `frontend/next.config.ts` proxy configuration
- Lihat browser console untuk errors

## Contributing

Ikuti aturan di `AGENTS.md` untuk kontribusi kode.

## License

MIT

## Disclaimer

PumpWatch adalah alat riset, bukan rekomendasi investasi. Semua keputusan trading adalah tanggung jawab pengguna. Tidak ada jaminan profit atau keamanan token. Skor momentum bukan prediksi pasti - selalu review risiko sebelum mengambil keputusan.
