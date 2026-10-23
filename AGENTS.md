# AGENTS.md --- Panduan AI Coding Agent

## Misi

Bangun PumpWatch, aplikasi pemantauan memecoin yang menampilkan kandidat
momentum dan risiko secara transparan. Baca `PRD.md` terlebih dahulu dan
ikuti scope MVP. Tujuan sistem adalah membantu riset, bukan menjamin
prediksi atau mengeksekusi transaksi.

## Prioritas

1.  Kebenaran data dan keamanan.
2.  Transparansi alasan scoring dan risk flags.
3.  Reliability dan observability.
4.  Pengujian.
5.  UX yang jelas.
6.  Optimasi hanya setelah bottleneck terukur.

## Scope yang tidak boleh dilanggar

-   Chain awal: Solana saja.
-   MVP read-only: jangan membuat buy/sell transaction, wallet signer,
    seed phrase/private key storage, copy trading, atau fitur live
    trading.
-   Gunakan rule-based scoring yang explainable; jangan menambahkan ML
    sebelum ada dataset dan evaluasi yang valid.
-   Jangan mengklaim token aman atau pump akan terjadi.
-   Jangan menganggap data yang hilang/stale sebagai aman atau bernilai
    nol tanpa alasan domain yang terdokumentasi.
-   Jangan mengarang data, API endpoint, response fields, atau kemampuan
    security provider. Verifikasi dokumentasi resmi.
-   Jangan menambahkan Redis, Kubernetes, microservices, atau dependensi
    besar tanpa alasan dan persetujuan yang jelas.

## Workflow sebelum coding

1.  Baca `PRD.md`, `README.md`, dan file konfigurasi yang relevan.
2.  Periksa struktur repository dan status Git; jangan menghapus atau
    menimpa pekerjaan yang sudah ada.
3.  Ringkas tujuan task, asumsi, dan file yang kemungkinan terdampak.
4.  Pecah task menjadi perubahan kecil yang dapat diuji.
5.  Jika ada keputusan penting yang belum ditentukan, pilih opsi paling
    sederhana yang aman dan dokumentasikan; tanyakan pengguna jika
    keputusan berisiko atau sulit dibalik.
6.  Jangan melakukan refactor besar di luar scope task.

## Arsitektur

-   Backend: Python + FastAPI.
-   Worker ingestion/scanning: Python.
-   Database: PostgreSQL.
-   Frontend: Next.js + TypeScript.
-   Alert: Telegram Bot API.
-   Market data provider: adapter terisolasi; implementasikan provider
    hanya berdasarkan dokumentasi terverifikasi.
-   Backend menjadi sumber kebenaran untuk scoring. Frontend tidak boleh
    menghitung ulang scoring secara terpisah.
-   Gunakan UTC untuk penyimpanan timestamp.
-   Pertahankan domain logic terpisah dari API, provider, database, dan
    notifikasi.

## Aturan implementasi

-   Gunakan type hints untuk Python dan tipe eksplisit untuk TypeScript.
-   Terapkan linting, formatting, schema validation, dan error handling
    konsisten.
-   Gunakan konfigurasi melalui environment variables/typed settings;
    sediakan `.env.example` tanpa nilai rahasia.
-   Jangan hard-code API keys, Telegram tokens, threshold, interval,
    atau URL provider yang dapat dikonfigurasi.
-   `.env` wajib masuk `.gitignore`.
-   Gunakan database migrations untuk perubahan schema.
-   Semua network calls harus punya timeout; retry hanya untuk error
    transient dengan backoff dan batas percobaan.
-   Tangani rate limits dengan hormat. Jangan mencoba mengakali batas
    provider.
-   Gunakan idempotency/deduplication pada ingestion dan alert.
-   Log harus terstruktur dan tidak boleh menyertakan secrets, private
    keys, seed phrases, atau data sensitif.
-   Gunakan pagination dan batas input pada endpoint yang mengembalikan
    daftar.
-   Validasi alamat token/pool dan gunakan chain + address sebagai
    identitas, bukan symbol.
-   Tandai data yang hilang, stale, atau konflik dengan status
    eksplisit.
-   Semua risk flags harus memiliki penjelasan, sumber, timestamp, dan
    status `pass`, `fail`, atau `unknown` sesuai kemampuan provider.
-   Hard-block risk harus mengalahkan momentum score.
-   Scoring harus menyimpan fitur input, komponen, versi aturan, data
    coverage, dan alasan skor.
-   Hindari look-ahead bias: fitur untuk sinyal historis hanya boleh
    memakai data yang tersedia pada timestamp sinyal.
-   Backtest wajib memasukkan sinyal gagal dan menjelaskan asumsi
    fee/slippage.
-   Jangan mengeluarkan klaim performa tanpa hasil evaluasi yang dapat
    direproduksi.

## Testing wajib

Tambahkan atau perbarui tes untuk setiap perubahan logika: - Unit tests
untuk normalisasi data, feature calculations, scoring, risk rules,
stale/missing data, dan cooldown. - Adapter tests memakai fixture/mock;
tes tidak boleh bergantung pada API live untuk hasil deterministik. -
Integration tests untuk database dan API bila relevan. - Tests untuk
rate-limit, timeout, retry, malformed payload, provider unavailable, dan
Telegram failure. - Frontend tests untuk loading, empty, stale, error,
dan normal states jika framework testing tersedia. - Uji batas angka dan
timezone. - Jalankan test, lint, type-check, dan build yang relevan
sebelum menyatakan task selesai.

## Keamanan

-   Tidak ada wallet/private key management pada MVP.
-   Jangan pernah meminta user menempelkan seed phrase/private key ke
    chat, issue, log, atau file proyek.
-   Redact secrets dari log/error.
-   Lindungi endpoint admin dan konfigurasi.
-   Validasi CORS, input, URL eksternal, dan payload provider.
-   Jangan menonaktifkan TLS verification untuk memperbaiki error.
-   Jangan mengubah firewall, service OS, permissions, atau konfigurasi
    sistem pengguna tanpa menjelaskan tujuan, manfaat, risiko, dan
    meminta persetujuan terlebih dahulu.
-   Jangan menjalankan perintah destruktif atau menghapus file tanpa
    memastikan scope dan backup/approval yang sesuai.
-   Jangan mengirim transaksi atau memindahkan dana.

## Aturan UI/copywriting

-   Gunakan label seperti "Momentum tinggi --- review risiko",
    "Watchlist", "Data belum cukup", dan "Diblokir oleh risk filter".
-   Jangan gunakan "pasti naik", "aman", "guaranteed profit", atau "buy
    now".
-   Tampilkan last updated, sumber data, data coverage, risk flags, dan
    alasan skor.
-   Jangan mengandalkan warna saja untuk status.
-   Jelaskan bahwa skor bukan probabilitas pump kecuali telah
    dikalibrasi dan diuji.

## Definition of Done untuk setiap task

1.  Implementasi sesuai scope dan pola repository.
2.  Tes relevan ditambahkan/diubah dan lulus.
3.  Lint/type-check/build yang tersedia lulus atau kegagalannya
    dijelaskan.
4.  Dokumentasi/config/schema diperbarui bila perlu.
5.  Tidak ada secret atau transaksi nyata.
6.  Ringkasan akhir menyebut perubahan, file utama, perintah tes dan
    hasilnya, asumsi, serta pekerjaan lanjutan.
7.  Jangan menyatakan selesai jika belum menjalankan pemeriksaan yang
    diklaim.

## Format respons AI saat bekerja

Sebelum task kompleks: - Tujuan - Rencana singkat - Asumsi/risiko

Setelah task: - Yang diubah - File utama - Cara menjalankan - Tes yang
dijalankan dan hasilnya - Batasan/risiko yang tersisa - Next step yang
disarankan

