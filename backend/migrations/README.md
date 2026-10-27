# Database Migrations

Migrations are plain SQL files executed in order.

## Running migrations

```bash
# Install PostgreSQL client if needed
sudo dnf install postgresql  # Fedora/RHEL
# or: sudo apt install postgresql-client  # Debian/Ubuntu

# Create database
createdb pumpwatch

# Run all migrations
psql -d pumpwatch -f migrations/001_initial_schema.sql
psql -d pumpwatch -f migrations/003_post_mvp_features.sql
```

## Migration naming

`XXX_description.sql` where XXX is sequential number (001, 002, etc.)

## Current migrations

### 001_initial_schema.sql
Initial tables for tokens, pools, and market snapshots:
- `tokens` - token metadata (chain, address, symbol, name)
- `pools` - pool/pair metadata
- `market_snapshots` - market data snapshots

### 003_post_mvp_features.sql
Post-MVP feature tables:

**Historical Archive**
- `momentum_snapshots` - historical momentum scores
- `risk_snapshots` - historical risk assessments

**Advanced Alerts**
- `alert_rules` - user-defined alert rules (global & per-token)
- `alert_cooldowns` - cooldown tracking per pair/rule

**Dashboard Analytics**
- `momentum_aggregates` - aggregated momentum metrics
- `risk_aggregates` - aggregated risk metrics

**Backtesting**
- `backtest_runs` - backtest configuration & metadata
- `backtest_trades` - simulated trades results

## Migrating to new version

If you already have database running:
```bash
# Backup first!
pg_dump pumpwatch > backup.sql

# Run new migration
psql -d pumpwatch -f backend/migrations/003_post_mvp_features.sql

# Verify tables created
psql -d pumpwatch -c "\dt"
```

## Database schema (Post-MVP)

```
tokens ──┬── market_snapshots (historical market data)
         ├── momentum_snapshots (Post-MVP)
         └── risk_snapshots (Post-MVP)

pools ──┴── market_snapshots

signals ──┬── backtest_trades (Post-MVP)

alert_rules ── alert_cooldowns (Post-MVP)
              └── backtest_trades (via signals)

momentum_aggregates (Post-MVP)
risk_aggregates (Post-MVP)
backtest_runs (Post-MVP)
```
