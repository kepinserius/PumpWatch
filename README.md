# PumpWatch --- Memecoin Momentum & Risk Scanner

PumpWatch adalah scanner memecoin yang membantu mengidentifikasi perubahan aktivitas pasar dan memaparkan risiko token secara transparan. Sistem tidak menjamin kenaikan harga dan tidak mengeksekusi transaksi pada MVP.

## Fitur MVP

- ✅ **Solana-only** read-only scanner
- ✅ **DexScreener integration** untuk market data
- ✅ **Risk engine** dengan liquidity checks, data quality validation
- ✅ **Momentum scoring** rule-based 6 komponen (0-100)
- ✅ **Dashboard** Next.js dengan watchlist & price charts
- ✅ **Telegram alerts** dengan cooldown & deduplication
- ✅ **API endpoints** untuk tokens, scoring, snapshots
- ✅ **Comprehensive tests** 28 tests passing

## Tech Stack

**Backend:**
- Python 3.12+ + FastAPI
- PostgreSQL untuk storage
- asyncpg untuk async database
- httpx untuk API calls
- pytest untuk testing

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

# Run migrations
psql -d pumpwatch -f backend/migrations/001_initial_schema.sql
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

# Build frontend
npm run build
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
Docs: `http://localhost:8000/docs`

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
pytest tests/test_api.py -v

# Run with coverage
pytest --cov=pumpwatch tests/
```

## API Endpoints

### Health
- `GET /health` — liveness check
- `GET /ready` — readiness check (database connectivity)

### Providers
- `GET /api/v1/providers/health` — DexScreener status

### Tokens
- `GET /api/v1/tokens` — list tokens (pagination)
- `GET /api/v1/tokens/{chain}/{address}` — token detail
- `GET /api/v1/tokens/{chain}/{address}/score` — risk + momentum score
- `GET /api/v1/tokens/{chain}/{address}/snapshots` — market history

### Admin
- `POST /api/v1/admin/scan?chain=solana` — trigger manual scan

## Architecture

```
DexScreener API
     ↓
Provider Adapter → Validation → Database (PostgreSQL)
     ↓                              ↓
Risk Engine + Momentum Engine      ↓
     ↓                              ↓
Signal Evaluator ← ← ← ← ← ← ← ← ←
     ↓
     ├→ FastAPI (Dashboard)
     └→ Telegram Alerts
```

## Prinsip

1. **Risk-first**: Hard-block risk mengalahkan momentum score
2. **Explainable**: Semua skor dapat diaudit dengan komponen dan coverage
3. **No false certainty**: Label "potensi naik" bukan jaminan
4. **Data provenance**: Tampilkan sumber, waktu, dan status data
5. **Fail safely**: Data missing/stale = unknown, bukan aman

## Dokumentasi Lengkap

- `PRD.md` — Product requirements, scope, architecture
- `AGENTS.md` — AI coding agent instructions
- `backend/migrations/README.md` — Database migration guide

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

**Frontend can't connect to backend:**
- Pastikan backend running di port 8000
- Check `frontend/next.config.ts` proxy configuration
- Lihat browser console untuk errors

**No Telegram alerts:**
- Verify `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_CHAT_ID` di `.env`
- Test manual: `/api/v1/admin/scan?chain=solana`
- Check backend logs untuk errors

## Contributing

Ikuti aturan di `AGENTS.md` untuk kontribusi kode.

## License

MIT

## Disclaimer

PumpWatch adalah alat riset, bukan rekomendasi investasi. Semua keputusan trading adalah tanggung jawab pengguna. Tidak ada jaminan profit atau keamanan token.
