# PRD --- Memecoin Momentum & Risk Scanner

**Nama kerja:** PumpWatch (nama sementara)\
**Versi dokumen:** 2.0\
**Status:** Updated untuk Post-MVP features\
**Tujuan utama:** Membantu pengguna menemukan dan mengevaluasi token
memecoin yang menunjukkan momentum awal, sambil menampilkan risiko
secara transparan. Sistem bukan peramal harga dan tidak menjamin profit.

## 1. Ringkasan Produk

PumpWatch adalah aplikasi pemantauan pasar memecoin yang mengumpulkan
data token dan pool DEX, memfilter kandidat berdasarkan kualitas data
dan risiko, menghitung skor momentum berbasis aturan yang dapat
dijelaskan, lalu mengirim alert ke dashboard dan Telegram.

Versi awal berfokus pada **Solana**, bersifat **read-only**, dan tidak
mengirim transaksi atau menyimpan private key. Pengguna tetap memutuskan
sendiri apakah akan melakukan riset atau transaksi.

### Prinsip produk

1.  **Risk-first:** token dengan risiko kritis tidak boleh dipromosikan
    hanya karena skor momentum tinggi.
2.  **Explainable:** setiap skor harus disertai alasan, data pendukung,
    timestamp, dan indikator yang belum tersedia.
3.  **No false certainty:** label seperti "potensi naik" bukan jaminan.
    Hindari bahasa "pasti pump", "aman", atau "profit terjamin".
4.  **Data provenance:** tampilkan sumber, waktu pengambilan, usia data,
    dan status kelengkapan data.
5.  **Paper-first:** validasi sinyal melalui historis dan paper trading
    sebelum mempertimbangkan eksekusi otomatis.
6.  **Fail safely:** bila data penting stale, hilang, atau sumber API
    gagal, tandai data sebagai tidak diketahui dan jangan menganggapnya
    aman.

## 2. Masalah dan Peluang

Pasar memecoin bergerak cepat, datanya tersebar, dan token baru dapat
memiliki likuiditas tipis, distribusi holder terkonsentrasi, aktivitas
bot, atau risiko kontrak. Pemeriksaan manual terhadap banyak token
memakan waktu dan mudah menghasilkan keputusan emosional.

Produk ini menyatukan pemantauan, filter, scoring, dan alert dalam satu
alur. Nilai produk bukan kemampuan menebak pemenang, tetapi mempercepat
riset dan mendisiplinkan proses seleksi.

## 3. Sasaran Pengguna

### Persona utama

Pengguna individu yang baru mempelajari trading memecoin, nyaman memakai
dashboard web, dan ingin membuat watchlist serta memeriksa sinyal
sebelum mengambil keputusan.

### Kebutuhan pengguna

-   Menemukan token/pool baru atau yang mulai aktif.
-   Melihat perubahan volume, harga, likuiditas, dan transaksi
    pembeli/penjual.
-   Memahami alasan token masuk watchlist.
-   Mengetahui risiko dan data yang belum dapat diverifikasi.
-   Mendapat alert yang bisa ditindaklanjuti tanpa harus menatap chart
    terus-menerus.
-   Mengevaluasi apakah alert historis punya nilai, setelah biaya dan
    slippage.

### Bukan target MVP

-   High-frequency trading.
-   Jaminan prediksi pump.
-   Auto-buy/auto-sell atau pengelolaan wallet.
-   Menggantikan audit keamanan kontrak profesional.
-   Menyarankan investasi personal atau menjanjikan return.

## 4. Ruang Lingkup

### In scope --- MVP

-   Solana sebagai chain pertama.
-   Penemuan pool/token melalui API data DEX.
-   Normalisasi data harga, volume, likuiditas, transaksi, dan waktu.
-   Filter awal untuk data tidak valid, likuiditas rendah, dan risiko
    yang diketahui.
-   Momentum score 0--100 berbasis rule engine.
-   Risk flags terpisah dari momentum score.
-   Dashboard watchlist dan detail token.
-   Telegram alert dengan cooldown/deduplication.
-   Penyimpanan snapshot dan riwayat sinyal.
-   Backtesting sederhana dan paper-trading simulation.
-   Konfigurasi batas skor dan filter melalui environment/config.
-   Logging, retry, rate-limit handling, health checks, dan dokumentasi.

### Out of scope --- MVP

-   Eksekusi transaksi on-chain.
-   Meminta atau menyimpan seed phrase/private key.
-   Copy-trading.
-   ML yang dilatih untuk prediksi return sebelum tersedia dataset dan
    evaluasi yang layak.
-   Multi-chain.
-   Social sentiment scraping sebagai sinyal utama.
-   Klaim keamanan berdasarkan satu sumber saja.

## 5. Asumsi dan Batasan

-   Sumber data eksternal dapat berubah, membatasi rate, atau mengalami
    downtime.
-   API market data tidak selalu menyediakan data holder, mint
    authority, freeze authority, LP lock, atau distribusi wallet yang
    lengkap.
-   Pemeriksaan keamanan harus memakai sumber yang benar-benar mendukung
    chain/token tersebut. Jangan mengarang hasil pemeriksaan.
-   Pool DEX bukan selalu representasi seluruh likuiditas token.
-   Harga, volume, market cap, dan FDV dapat tidak lengkap atau
    menyesatkan untuk token baru.
-   Semua timestamp disimpan dalam UTC dan ditampilkan dalam zona waktu
    pengguna.
-   Data yang tidak tersedia bernilai `unknown`, bukan `false` atau
    "aman".

## 6. Alur Pengguna

1.  Scanner mengambil kandidat token/pool dari sumber yang
    dikonfigurasi.
2.  Sistem memvalidasi alamat, chain, pool, timestamp, dan kelengkapan
    data.
3.  Data dinormalisasi dan disimpan sebagai snapshot.
4.  Risk engine mengevaluasi hard-stop rules dan risk flags.
5.  Momentum engine menghitung fitur dan skor berdasarkan data yang
    tersedia.
6.  Alert engine membandingkan skor dengan threshold, menerapkan
    cooldown, lalu mengirim notifikasi.
7.  Pengguna membuka detail token untuk melihat alasan skor, risiko,
    grafik, sumber, dan waktu update.
8.  Sinyal dicatat untuk evaluasi historis; paper trading dapat
    mensimulasikan entry/exit tanpa dana nyata.

## 7. Persyaratan Fungsional

### FR-01 --- Token discovery

-   Sistem dapat mengambil kandidat dari endpoint resmi penyedia data
    yang dipilih.
-   Setiap kandidat minimal menyimpan chain, token address/mint,
    pool/pair address jika tersedia, simbol/nama jika tersedia, sumber,
    dan discovered_at.
-   Identitas token menggunakan chain + alamat, bukan simbol/nama.
-   Deduplicate token/pool agar satu pool tidak menghasilkan alert
    berulang tanpa alasan.

### FR-02 --- Market data ingestion

-   Ambil harga, volume per periode yang tersedia, likuiditas, transaksi
    buy/sell, perubahan harga, dan timestamp.
-   Simpan raw response terbatas untuk debugging sesuai kebijakan
    retensi; jangan menyimpan secret.
-   Terapkan timeout, retry dengan exponential backoff + jitter, dan
    rate-limit handling.
-   Tandai stale data jika melewati TTL konfigurasi.
-   Jangan menganggap data dari dua provider memiliki definisi metrik
    yang sama tanpa normalisasi.

### FR-03 --- Data validation

-   Validasi tipe, rentang, timestamp, alamat, dan nilai negatif yang
    tidak masuk akal.
-   Nilai yang hilang harus tetap `null/unknown`.
-   Data dengan timestamp masa depan yang tidak masuk akal atau terlalu
    tua tidak boleh memicu alert prioritas tinggi.
-   Catat alasan validasi gagal.

### FR-04 --- Risk engine

-   Menghasilkan `risk_flags[]`, `risk_level`, dan `hard_block`.
-   Risiko kritis dapat memblokir alert kandidat meski momentum score
    tinggi.
-   Pemeriksaan harus menunjukkan sumber, waktu pemeriksaan, dan tingkat
    keyakinan.
-   Jika pemeriksaan tidak didukung atau gagal, statusnya `unknown`;
    tidak boleh disebut lolos.
-   Contoh pemeriksaan, tergantung dukungan data: likuiditas di bawah
    minimum, pool terlalu baru, konsentrasi holder ekstrem, mint/freeze
    authority, simulasi sell/honeypot, perubahan otoritas, dan indikasi
    likuiditas dapat ditarik.
-   Jangan menyebut token "rug pull" sebagai fakta tanpa bukti; gunakan
    "indikasi risiko" dan jelaskan dasar flag.

### FR-05 --- Momentum scoring

-   Skor rentang 0--100.
-   Simpan skor total, skor per komponen, fitur input, versi aturan, dan
    penjelasan yang bisa dibaca pengguna.
-   Skor tidak boleh dihitung dari fitur yang tidak tersedia seolah-olah
    nilainya nol atau aman; lakukan renormalisasi bobot fitur yang
    tersedia dan tampilkan coverage.
-   Hard-stop risk tetap mengalahkan skor.
-   Threshold dan bobot dapat diubah lewat konfigurasi, bukan hard-coded
    di banyak tempat.

### FR-06 --- Alerting

-   Kirim alert Telegram jika skor dan filter memenuhi konfigurasi.
-   Alert minimal berisi token/pool, chain, skor, perubahan harga/volume
    dengan rentang waktu jelas, likuiditas, risk flags, data coverage,
    timestamp, dan tautan explorer/chart yang berasal dari sumber
    tepercaya.
-   Gunakan cooldown per token/pool dan deduplication key.
-   Jangan kirim ulang alert identik tanpa perubahan material.
-   Jika Telegram gagal, antrekan dan retry secara terbatas, lalu log
    kegagalan.

### FR-07 --- Dashboard

Halaman MVP: 1. **Overview:** jumlah kandidat, alert terbaru, status
sumber data, waktu update terakhir. 2. **Scanner/Watchlist:** tabel
kandidat yang dapat difilter dan diurutkan. 3. **Token detail:**
chart/data historis, skor, faktor penyusun, risiko, sumber, dan riwayat
alert. 4. **Signals history:** seluruh sinyal termasuk yang tidak
berhasil. 5. **Settings:** threshold, interval, minimum liquidity,
cooldown, dan preferensi alert. 6. **System health:** status API, queue,
worker, dan database.

### FR-08 --- Historis dan evaluasi

-   Simpan setiap sinyal saat terpicu beserta data yang tersedia pada
    saat itu.
-   Catat harga referensi saat sinyal, lalu harga pada horizon yang
    dikonfigurasi (misalnya 5m, 15m, 1h, 4h, 24h bila data memadai).
-   Catat maximum favorable excursion (MFE), maximum adverse excursion
    (MAE), perubahan harga setelah biaya/slippage asumsi, serta apakah
    token/pool tidak lagi memiliki data.
-   Gunakan data historis yang tersedia pada waktu sinyal saja untuk
    menghindari look-ahead bias.
-   Laporkan jumlah sampel dan confidence/ketidakpastian; jangan hanya
    menampilkan persentase win rate.
-   Masukkan token yang rugi, tidak likuid, atau hilang; jangan hanya
    menyimpan pemenang.

### FR-09 --- Paper trading

-   Tidak mengeksekusi transaksi riil.
-   Simulasikan biaya, slippage, ukuran posisi, entry, exit, dan batas
    waktu.
-   Parameter simulasi harus terlihat dan bisa diubah.
-   Hindari menganggap harga last-traded bisa dieksekusi pada ukuran
    posisi apa pun.
-   Hasil simulasi bukan bukti profit masa depan.

### FR-10 --- Auditability

-   Setiap alert dapat ditelusuri ke snapshot data, versi scoring, dan
    hasil risk checks.
-   Simpan perubahan konfigurasi penting dengan timestamp.
-   Log tidak boleh berisi token API, password, private key, seed
    phrase, atau data sensitif.

## 8. Momentum Scoring Awal

Bobot awal berikut adalah hipotesis untuk eksperimen, bukan model yang
terbukti.

  ------------------------------------------------------------------------
  Komponen                                Bobot awal Contoh pengukuran
  --------------------- ---------------------------- ---------------------
  Pertumbuhan volume                             25% Volume window pendek
                                                     dibanding baseline
                                                     sebelumnya

  Buy pressure                                   20% Rasio nilai/volume
                                                     buy terhadap sell,
                                                     jika definisi
                                                     provider jelas

  Kualitas likuiditas                            20% Likuiditas absolut,
                                                     stabilitas, dan
                                                     estimasi slippage

  Pertumbuhan aktivitas                          15% Transaksi
                                                     unik/pembeli unik
                                                     bila data tersedia;
                                                     jangan menyamakan
                                                     transaksi dengan
                                                     orang

  Momentum harga                                 10% Return dalam beberapa
                                                     window dan perubahan
                                                     volatilitas

  Kualitas/umur pool                             10% Usia pool dan
                                                     kecukupan observasi;
                                                     bukan otomatis makin
                                                     muda makin baik
  ------------------------------------------------------------------------

### Aturan scoring

-   Skor komponen dinormalisasi ke 0--100 dengan metode yang
    terdokumentasi.
-   Volume spike dihitung relatif terhadap baseline token itu sendiri
    jika cukup histori, bukan hanya dibanding token lain.
-   Bila tidak ada baseline, beri status `insufficient_history`.
-   Hindari menghitung buy/sell pressure dari data yang tidak sebanding.
-   Data coverage ditampilkan terpisah, misalnya 72% fitur tersedia.
-   Jangan menyebut skor sebagai probabilitas pump kecuali sudah
    dikalibrasi dengan data out-of-sample.
-   Bobot harus dievaluasi lewat backtest dan paper trading; jangan
    optimasi hanya untuk histori yang sama.

### Contoh kategori UI

-   80--100: "Momentum tinggi --- perlu review risiko"
-   65--79: "Watchlist"
-   Di bawah 65: "Belum memenuhi threshold"
-   Hard-block: "Diblokir oleh risk filter" Label ini adalah kategori
    internal produk, bukan rekomendasi membeli.

## 9. Hard Filters dan Risk Flags

Konfigurasi awal perlu diuji, bukan dianggap standar universal: -
Likuiditas minimum yang dapat disetel per chain. - Pool/token tanpa data
pasar yang cukup: tandai `insufficient_data`. - Harga/volume stale:
jangan kirim alert prioritas tinggi. - Lonjakan volume ekstrem dengan
likuiditas tidak memadai: flag. - Konsentrasi holder ekstrem jika data
pemilik wallet yang dapat dipercaya tersedia. - Otoritas mint/freeze
atau risiko kontrak yang relevan untuk token program/chain tersebut. -
Honeypot/sell simulation hanya bila provider mendukung chain dan metode
token yang tepat. - Sumber data saling bertentangan: tampilkan
discrepancy dan turunkan confidence. - Token/pool yang sudah tidak aktif
atau tidak dapat diperdagangkan: blokir dari kandidat aktif.

Jangan menerapkan satu pemeriksaan EVM pada Solana. Pemeriksaan harus
sesuai dengan arsitektur chain dan token program yang sebenarnya.

## 10. Arsitektur Teknis

### Stack yang disarankan

-   **Backend/API:** Python 3.12+ dengan FastAPI.
-   **Worker/ingestion:** Python async worker; scheduler sederhana pada
    MVP.
-   **Database:** PostgreSQL.
-   **Cache/queue:** mulai tanpa Redis bila volume rendah; tambahkan
    Redis hanya saat kebutuhan terbukti.
-   **Frontend:** Next.js + TypeScript.
-   **Charts:** library chart yang aktif dipelihara dan mendukung time
    series.
-   **Notifications:** Telegram Bot API.
-   **Market data:** adapter provider untuk DEX Screener dan/atau
    GeckoTerminal; periksa dokumentasi, batas rate, cakupan chain, dan
    syarat layanan sebelum implementasi.
-   **Testing:** pytest, lint/type checking Python, test frontend, dan
    integration tests untuk adapter API.
-   **Deployment:** lokal terlebih dahulu; kemudian VPS/container bila
    perlu.

### Diagram komponen

``` text
External Market Data APIs
          |
          v
Provider Adapters -> Validation/Normalization -> PostgreSQL snapshots
                                             |
                                             v
                                    Feature Calculator
                                             |
                          +------------------+----------------+
                          v                                   v
                    Risk Engine                         Momentum Engine
                          +------------------+----------------+
                                             |
                                             v
                                      Signal Evaluator
                                      /             \
                                     v               v
                                FastAPI API     Alert Queue/Worker
                                     |               |
                                     v               v
                              Next.js Dashboard   Telegram Bot
                                     |
                                     v
                              History/Backtest
```

### Batas tanggung jawab

-   Provider adapter hanya mengambil dan memetakan data.
-   Domain services menghitung fitur, risk flags, dan skor.
-   API layer tidak berisi logika market yang kompleks.
-   Frontend tidak menghitung ulang skor secara independen; backend
    adalah sumber kebenaran.
-   Notification worker tidak mengubah skor; hanya mengirim hasil
    evaluasi.
-   Semua waktu disimpan UTC.

## 11. Model Data Awal

### `tokens`

-   `id`
-   `chain`
-   `address` (unique bersama chain)
-   `symbol` nullable
-   `name` nullable
-   `first_seen_at`
-   `metadata_json` terbatas

### `pools`

-   `id`
-   `chain`
-   `pool_address`
-   `base_token_address`
-   `quote_token_address`
-   `dex_id` nullable
-   `created_at` nullable
-   unique `(chain, pool_address)`

### `market_snapshots`

-   `id`
-   `token_id`, `pool_id`
-   `observed_at`
-   `source`
-   `price_usd` nullable
-   `liquidity_usd` nullable
-   `volume_5m/1h/6h/24h` nullable jika tersedia
-   `price_change_*` nullable
-   `buys_*`, `sells_*` nullable jika tersedia
-   `raw_data_ref` atau JSON yang dibatasi ukurannya
-   `data_quality_status`

### `risk_assessments`

-   `id`
-   `token_id`, `pool_id`
-   `checked_at`
-   `risk_level`
-   `hard_block`
-   `flags_json`
-   `sources_json`
-   `coverage`
-   `rules_version`

### `signals`

-   `id`
-   `token_id`, `pool_id`
-   `created_at`
-   `score`
-   `score_components_json`
-   `feature_snapshot_json`
-   `risk_assessment_id`
-   `rules_version`
-   `status`

### `alerts`

-   `id`
-   `signal_id`
-   `channel`
-   `dedupe_key`
-   `sent_at` nullable
-   `status`
-   `attempt_count`
-   `last_error` sanitized

### `paper_trades`

-   `id`
-   `signal_id`
-   `entry_timestamp`
-   `reference_entry_price`
-   `simulated_entry_price`
-   `position_size`
-   `fee_assumption`
-   `slippage_assumption`
-   `exit_timestamp` nullable
-   `simulated_exit_price` nullable
-   `net_return` nullable
-   `status`

### `provider_health`

-   `provider`
-   `checked_at`
-   `status`
-   `latency_ms`
-   `rate_limit_state`
-   `error_code` sanitized

Indeks dan partitioning harus mengikuti beban yang terukur. Jangan
menambahkan kompleksitas database sebelum kebutuhan terlihat.

## 12. API Internal (contoh rancangan)

-   `GET /health` --- liveness.
-   `GET /ready` --- kesiapan aplikasi dan database.
-   `GET /api/v1/tokens` --- filter/sort kandidat.
-   `GET /api/v1/tokens/{chain}/{address}` --- detail token.
-   `GET /api/v1/tokens/{chain}/{address}/snapshots` --- histori market.
-   `GET /api/v1/signals` --- riwayat sinyal dengan pagination.
-   `GET /api/v1/signals/{id}` --- detail skor, fitur, dan risiko.
-   `GET /api/v1/providers/health` --- status provider.
-   `GET /api/v1/settings` --- konfigurasi non-secret.
-   `PATCH /api/v1/settings` --- mengubah konfigurasi dengan validasi
    dan audit.
-   `POST /api/v1/admin/scan` --- pemicu scan manual, dilindungi
    autentikasi jika aplikasi dipublikasikan.

Semua endpoint perlu schema validation, pagination, batas ukuran
request, penanganan error konsisten, dan dokumentasi OpenAPI.

## 13. Non-Functional Requirements

### Reliability

-   Kegagalan satu provider tidak boleh menjatuhkan seluruh aplikasi.
-   Timeout dan retry terbatas.
-   Idempotency pada ingest dan alert.
-   Health status harus membedakan `healthy`, `degraded`, dan
    `unavailable`.

### Performance

-   Target awal: dashboard dapat menampilkan hasil tersimpan dalam \<2
    detik pada lingkungan lokal yang wajar.
-   Interval scan dapat dikonfigurasi dan harus mematuhi rate limit
    provider.
-   Jangan mengklaim real-time jika data berasal dari polling; tampilkan
    last updated.

### Security

-   Tidak ada private key/seed phrase dalam MVP.
-   Secret API dan Telegram token disimpan di environment/secret
    manager, bukan source code.
-   `.env` masuk `.gitignore`; sediakan `.env.example` tanpa secret.
-   Batasi CORS, validasi input, lindungi endpoint admin, dan gunakan
    TLS pada deployment publik.
-   Hindari SQL injection melalui ORM/query parameterization.
-   Dependensi dipin/di-lock dan diperbarui secara teratur.
-   Jangan log credential atau full raw response yang berisi secret.
-   Dashboard publik harus memiliki autentikasi atau tidak mengekspos
    konfigurasi/admin endpoints.

### Observability

-   Structured logs dengan request/scan IDs.
-   Metrics: request count, latency, provider errors, scan duration,
    stale data count, alert success/failure.
-   Alert jika provider gagal terus-menerus atau data berhenti
    diperbarui.

### Maintainability

-   Type hints, linting, formatting, docstrings untuk logika nontrivial.
-   Unit tests untuk scoring dan risk rules.
-   Provider adapters dapat diganti tanpa menulis ulang domain logic.

## 14. UI/UX Requirements

-   Tampilkan "last updated" dan sumber data di semua halaman relevan.
-   Gunakan warna sebagai bantuan, bukan satu-satunya pembeda status;
    sertakan teks/icon.
-   Setiap flag memiliki tooltip/penjelasan sederhana.
-   Jangan memakai label "safe token".
-   Tabel mendukung filter chain, usia pool, likuiditas, skor, risk
    level, dan waktu update.
-   Detail token menampilkan chart bersama konteks likuiditas dan
    volume.
-   Tampilkan empty/error/stale states yang jelas.
-   Link eksternal harus berasal dari data tervalidasi; jangan membentuk
    URL explorer dari string tak tepercaya tanpa validasi.

## 15. Backtesting dan Metrik Keberhasilan

### Metrik produk

-   Proporsi alert yang terkirim dengan data tidak stale.
-   Latensi dari observasi provider ke alert.
-   Duplicate alert rate.
-   Persentase sinyal dengan data coverage di atas batas minimum.
-   Uptime worker/provider.

### Metrik kualitas sinyal

Definisikan sebelum evaluasi, misalnya: - Forward return pada horizon
5m, 15m, 1h, 4h, 24h. - MFE dan MAE setelah sinyal. - Return bersih
dengan asumsi biaya dan slippage. - Precision untuk target yang telah
ditentukan sebelumnya. - Drawdown dan distribusi kerugian. - Hasil
menurut usia pool, likuiditas, dan kondisi pasar.

### Aturan evaluasi

-   Pisahkan train/tuning dan periode out-of-sample.
-   Hindari look-ahead bias, survivorship bias, dan memilih hanya token
    yang masih hidup.
-   Simpan semua sinyal, termasuk sinyal gagal.
-   Uji sensitivitas terhadap biaya, slippage, keterlambatan alert, dan
    likuiditas.
-   Bandingkan dengan baseline sederhana.
-   Jangan mengklaim model berhasil hanya dari beberapa contoh atau win
    rate tanpa ukuran sampel.
-   Sebelum paper trading, tetapkan definisi keberhasilan dan horizon
    secara eksplisit.

## 16. Tahapan Implementasi

### Phase 0 --- Repository foundation

-   Buat monorepo atau folder backend/frontend yang jelas.
-   Tambahkan README, PRD, AGENTS.md, `.env.example`, formatter, linter,
    dan test setup.
-   Buat konfigurasi typed dan logging.
-   Kriteria selesai: proyek dapat dijalankan lokal dari dokumentasi.

### Phase 1 --- Data ingestion

-   Implementasikan satu provider adapter terlebih dahulu.
-   Simpan token, pool, dan snapshot.
-   Tangani timeout, rate limits, retries, dan data stale.
-   Kriteria selesai: tes adapter dengan fixture/mock dan hasil snapshot
    tervalidasi.

### Phase 2 --- Scanner + risk rules

-   Implementasikan hard filters dan risk flags yang benar-benar
    didukung sumber data.
-   Tambahkan score komponen awal dan alasan yang bisa dijelaskan.
-   Kriteria selesai: unit tests untuk ambang, missing data, stale data,
    dan hard blocks.

### Phase 3 --- Dashboard + Telegram

-   Tampilkan overview, watchlist, detail token, riwayat alert.
-   Implementasikan dedupe/cooldown dan Telegram notification.
-   Kriteria selesai: alert dapat ditelusuri ke snapshot dan rules
    version.

### Phase 4 --- History + backtest (SELESAI)

-   Rekam outcome pada horizon terpilih.
-   Implementasikan simulasi biaya/slippage dan laporan hasil.
-   Kriteria selesai: laporan mencakup sinyal gagal, missing outcomes,
    sample size, dan limitations.
-   **Implemented:** Historical archive, backtesting engine, analytics

### Phase 5 --- Advanced alerts + analytics (SELESAI)

-   Alert rules per-token & global, cooldown per pair
-   Dashboard analytics dengan momentum/risk trends
-   Kriteria selesai: alert rules CRUD, analytics endpoints, frontend UI
-   **Implemented:** AlertManager, AnalyticsService, frontend settings

### Phase 6 --- Pertimbangkan ekspansi

Hanya setelah MVP stabil: provider tambahan, chain tambahan, fitur
sosial, model statistik/ML, atau eksekusi transaksi. Setiap fitur baru
memerlukan evaluasi risiko dan review terpisah.

## 17. Definition of Done (MVP)

MVP dianggap selesai bila: - \[ \] Data token/pool dapat diambil dari
satu provider yang didukung dan disimpan. - \[ \] Data invalid/stale
ditandai, bukan disembunyikan. - \[ \] Scoring deterministik dan
memiliki unit tests. - \[ \] Risk flags terpisah dari momentum score. -
\[ \] Hard-block mengalahkan skor momentum. - \[ \] Dashboard
menampilkan kandidat, detail, alasan skor, risiko, dan last updated. -
\[ \] Telegram alert berfungsi dengan dedupe/cooldown. - \[ \] Riwayat
sinyal tersimpan, termasuk yang buruk. - \[ \] Backtest/paper-trading
mencatat biaya/slippage asumsi. - \[ \] Tidak ada eksekusi transaksi
atau private key pada MVP. - \[ \] `.env.example`, README, migration,
test commands, dan troubleshooting tersedia. - \[ \] Setup lokal dapat
direproduksi dari dokumentasi.

## 18. Risiko Proyek

  -------------------------------------------------------------------------
  Risiko                    Dampak                  Mitigasi
  ------------------------- ----------------------- -----------------------
  API berubah atau          Data terlambat/hilang   Adapter, backoff,
  rate-limited                                      provider health, cache

  Wash trading/bot activity False positive          Kombinasi indikator,
                                                    confidence, manual
                                                    review

  Likuiditas semu/tipis     Slippage/exit sulit     Minimum liquidity dan
                                                    simulasi slippage

  Holder concentration      Risk terlewat           Status unknown dan
  tidak lengkap                                     sumber tambahan

  Survivorship/look-ahead   Backtest menipu         Simpan snapshot saat
  bias                                              sinyal dan semua
                                                    outcome

  Overfitting bobot         Kinerja buruk di masa   Out-of-sample dan
                            depan                   baseline

  Alert terlalu banyak      Pengguna mengabaikan    Cooldown, dedupe,
                            alert                   threshold

  Secret bocor              Penyalahgunaan bot/API  Environment secrets,
                                                    `.gitignore`, redaction

  Salah paham skor sebagai  Kerugian finansial      Copy UI yang hati-hati
  kepastian                                         dan transparansi
                                                    batasan
  -------------------------------------------------------------------------

## 19. Keputusan yang Harus Dipertahankan

-   MVP Solana-only.
-   Read-only; no wallet connection and no live trading.
-   Rule-based scoring dulu, ML belakangan.
-   Risk flags terpisah dari momentum.
-   Missing/stale data tidak pernah dianggap aman.
-   Backtesting dan paper trading wajib sebelum live execution.
-   Semua skor dan alert dapat diaudit.
-   API provider, bobot, threshold, dan interval harus configurable.
-   Jangan menambahkan microservices, Redis, Kubernetes, atau
    infrastruktur kompleks sebelum diperlukan.

## 20. Referensi Teknis

Verifikasi dokumentasi dan rate limits saat implementasi; jangan
mengandalkan endpoint yang tidak terdokumentasi. - DEX Screener API:
https://docs.dexscreener.com/api/reference - GeckoTerminal API guide:
https://apiguide.geckoterminal.com/ - Solana documentation:
https://solana.com/docs - FastAPI: https://fastapi.tiangolo.com/ -
PostgreSQL: https://www.postgresql.org/docs/ - Next.js:
https://nextjs.org/docs - Telegram Bot API:
https://core.telegram.org/bots/api
