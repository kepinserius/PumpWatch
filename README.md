# PumpWatch --- Memecoin Momentum & Risk Scanner

PumpWatch adalah proyek scanner memecoin yang membantu mengidentifikasi
perubahan aktivitas pasar dan memaparkan risiko token. Sistem tidak
menjamin kenaikan harga dan tidak mengeksekusi transaksi pada MVP.

## Dokumen

-   `PRD.md`: kebutuhan produk, scope, arsitektur, data, scoring,
    testing, dan roadmap.
-   `AGENTS.md`: instruksi operasional untuk AI coding agent.

## MVP

-   Solana-only.
-   Read-only.
-   Market data ingestion.
-   Risk flags + explainable momentum scoring.
-   Dashboard + Telegram alerts.
-   Signal history, backtesting, dan paper trading.
-   Tanpa wallet/private key dan tanpa transaksi riil.

## Prinsip

Data missing/stale berarti unknown, bukan aman. Risiko kritis
mengalahkan skor momentum. Semua sinyal harus dapat diaudit. Backtesting
harus menghindari look-ahead dan survivorship bias serta memasukkan
biaya/slippage.

## Referensi

-   https://docs.dexscreener.com/api/reference
-   https://apiguide.geckoterminal.com/
-   https://solana.com/docs
-   https://fastapi.tiangolo.com/
-   https://nextjs.org/docs
