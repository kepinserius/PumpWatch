'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import Link from 'next/link';

const API_BASE = '/api/v1';

// ── Types ────────────────────────────────────────────────────────────────────
interface Signal {
  id: number;
  created_at: string;
  score: number;
  status: string;
  entry_price_usd: number | null;
  chain: string;
  address: string;
  symbol?: string;
  name?: string;
}

interface Outcome {
  return_5m: number | null;
  return_1h: number | null;
  return_24h: number | null;
  mfe: number | null;
  mae: number | null;
}

interface ProviderHealth {
  status: string;
  provider: string;
}

// ── API ──────────────────────────────────────────────────────────────────────
const fetchJson = async <T,>(url: string): Promise<T> => {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
};

// ── Helpers ──────────────────────────────────────────────────────────────────
const shortAddr = (addr: string, n = 6) => `${addr.slice(0, n)}…${addr.slice(-4)}`;

const fmtDate = (iso: string) =>
  new Date(iso).toLocaleString('id-ID', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  });

const scoreBadge = (score: number) => {
  if (score >= 80) return { bg: '#0f2a1a', text: '#22c55e', label: 'Tinggi' };
  if (score >= 65) return { bg: '#0f1e3a', text: '#4f8ef7', label: 'Watchlist' };
  return { bg: '#1c1c28', text: '#555b6e', label: 'Di bawah threshold' };
};

const statusBadge = (s: string) => {
  if (s === 'active') return { bg: '#0f2a1a', text: '#22c55e' };
  if (s === 'closed') return { bg: '#1c1c28', text: '#8b90a0' };
  return { bg: '#2a1f0a', text: '#f59e0b' };
};

const pctColor = (v: number) => (v >= 0 ? '#22c55e' : '#ef4444');
const pctFmt = (v: number) => `${v >= 0 ? '+' : ''}${(v * 100).toFixed(2)}%`;

// ── Components ────────────────────────────────────────────────────────────────
function NavBar({ providerHealth }: { providerHealth?: ProviderHealth }) {
  const isHealthy = providerHealth?.status === 'healthy';
  return (
    <nav style={{
      background: '#141720', borderBottom: '1px solid #252836',
      padding: '0 24px', height: '56px', display: 'flex',
      alignItems: 'center', justifyContent: 'space-between',
      position: 'sticky', top: 0, zIndex: 100,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ fontSize: '18px', fontWeight: 700, color: '#e8eaf0', letterSpacing: '-0.3px' }}>
          PumpWatch
        </span>
        <span style={{ fontSize: '11px', color: '#555b6e', background: '#1c1f2e', padding: '2px 8px', borderRadius: '4px', fontWeight: 500 }}>
          SOLANA
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <Link href="/" style={{ color: '#8b90a0', textDecoration: 'none', fontSize: '13px', fontWeight: 500 }}>
          Watchlist
        </Link>
        <Link href="/signals" style={{ color: '#e8eaf0', textDecoration: 'none', fontSize: '13px', fontWeight: 600, borderBottom: '2px solid #4f8ef7', paddingBottom: '2px' }}>
          Signals
        </Link>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#1c1f2e', padding: '4px 10px', borderRadius: '6px', fontSize: '12px' }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: isHealthy ? '#22c55e' : '#f59e0b', display: 'inline-block' }} />
          <span style={{ color: '#8b90a0' }}>{providerHealth?.provider ?? 'Provider'}</span>
          <span style={{ color: isHealthy ? '#22c55e' : '#f59e0b', fontWeight: 600 }}>{providerHealth?.status ?? '…'}</span>
        </div>
      </div>
    </nav>
  );
}

function OutcomeCard({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ background: '#1c1f2e', borderRadius: '8px', padding: '10px 12px' }}>
      <div style={{ color: '#555b6e', fontSize: '11px', marginBottom: '4px' }}>{label}</div>
      <div style={{ color: pctColor(value), fontWeight: 700, fontSize: '15px' }}>{pctFmt(value)}</div>
    </div>
  );
}

function SignalDetailPanel({ signal }: { signal: Signal }) {
  const { data: outcome, isLoading } = useQuery({
    queryKey: ['outcome', signal.id],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/signals/${signal.id}/outcome`);
      if (res.status === 404) return null;
      if (!res.ok) throw new Error('Failed');
      return res.json() as Promise<Outcome>;
    },
  });

  const sb = scoreBadge(signal.score);

  return (
    <div style={{ background: '#141720', border: '1px solid #252836', borderRadius: '12px', overflow: 'hidden', position: 'sticky', top: '72px' }}>
      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid #252836', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: '15px', color: '#e8eaf0' }}>
            Signal #{signal.id}
          </div>
          <div style={{ color: '#8b90a0', fontSize: '12px', marginTop: '2px' }}>
            {signal.symbol ?? shortAddr(signal.address)}
          </div>
        </div>
        <div style={{ background: sb.bg, color: sb.text, padding: '3px 8px', borderRadius: '5px', fontSize: '10px', fontWeight: 700, letterSpacing: '0.5px' }}>
          {sb.label.toUpperCase()}
        </div>
      </div>

      <div style={{ padding: '20px' }}>
        {/* Score display */}
        <div style={{ marginBottom: '20px', textAlign: 'center', padding: '16px', background: '#1c1f2e', borderRadius: '8px' }}>
          <div style={{ color: '#555b6e', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '8px' }}>
            Momentum Score
          </div>
          <div style={{ fontSize: '48px', fontWeight: 800, color: sb.text, lineHeight: 1 }}>
            {signal.score}
          </div>
          <div style={{ color: '#555b6e', fontSize: '11px', marginTop: '6px' }}>
            dari maksimum 100
          </div>
        </div>

        {/* Details */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
          {[
            { label: 'Chain', value: signal.chain.toUpperCase() },
            { label: 'Address', value: shortAddr(signal.address, 8) },
            { label: 'Entry Price', value: signal.entry_price_usd != null ? `$${signal.entry_price_usd.toFixed(8)}` : '—' },
            { label: 'Waktu Signal', value: fmtDate(signal.created_at) },
            { label: 'Status', value: signal.status },
          ].map(({ label, value }) => (
            <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#555b6e', fontSize: '12px' }}>{label}</span>
              <span style={{ color: '#e8eaf0', fontSize: '12px', fontWeight: 500 }}>{value}</span>
            </div>
          ))}
        </div>

        {/* Outcomes */}
        {isLoading ? (
          <div style={{ color: '#555b6e', fontSize: '12px', textAlign: 'center' }}>Memuat outcome…</div>
        ) : outcome ? (
          <div>
            <div style={{ color: '#555b6e', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '10px' }}>
              Outcome Aktual
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              {outcome.return_5m != null && <OutcomeCard label="5m Return" value={outcome.return_5m} />}
              {outcome.return_1h != null && <OutcomeCard label="1h Return" value={outcome.return_1h} />}
              {outcome.return_24h != null && <OutcomeCard label="24h Return" value={outcome.return_24h} />}
              {outcome.mfe != null && <OutcomeCard label="Max Favorable" value={outcome.mfe} />}
              {outcome.mae != null && <OutcomeCard label="Max Adverse" value={outcome.mae} />}
            </div>
          </div>
        ) : (
          <div style={{ background: '#1c1f2e', borderRadius: '8px', padding: '12px', color: '#555b6e', fontSize: '12px', textAlign: 'center' }}>
            Outcome belum tersedia
          </div>
        )}

        {/* Disclaimer */}
        <div style={{ marginTop: '16px', padding: '10px 12px', background: '#1c1f2e', borderRadius: '6px', fontSize: '11px', color: '#555b6e', lineHeight: '1.5' }}>
          WARNING: Skor bukan prediksi. Return aktual bisa berbeda signifikan. Ini adalah alat riset, bukan rekomendasi transaksi.
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function SignalsPage() {
  const [selected, setSelected] = useState<Signal | null>(null);

  const { data: signals, isLoading } = useQuery({
    queryKey: ['signals'],
    queryFn: () => fetchJson<Signal[]>(`${API_BASE}/signals?limit=100`),
    refetchInterval: 30000,
  });

  const { data: providerHealth } = useQuery({
    queryKey: ['providerHealth'],
    queryFn: () => fetchJson<ProviderHealth>(`${API_BASE}/providers/health`),
    refetchInterval: 60000,
  });

  const highCount = signals?.filter((s) => s.score >= 80).length ?? 0;
  const watchCount = signals?.filter((s) => s.score >= 65 && s.score < 80).length ?? 0;

  return (
    <div style={{ minHeight: '100vh', background: '#0d0f14' }}>
      <NavBar providerHealth={providerHealth} />

      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '24px' }}>
        {/* Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '12px', marginBottom: '24px' }}>
          {[
            { label: 'Total Signals', value: signals?.length ?? '—', sub: 'semua waktu' },
            { label: 'Momentum Tinggi', value: highCount, sub: 'skor ≥ 80' },
            { label: 'Watchlist', value: watchCount, sub: 'skor 65–79' },
            { label: 'Active', value: signals?.filter((s) => s.status === 'active').length ?? '—', sub: 'masih terbuka' },
          ].map(({ label, value, sub }) => (
            <div key={label} style={{ background: '#141720', border: '1px solid #252836', borderRadius: '10px', padding: '16px 20px' }}>
              <div style={{ color: '#555b6e', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '8px' }}>{label}</div>
              <div style={{ color: '#e8eaf0', fontSize: '22px', fontWeight: 700 }}>{value}</div>
              <div style={{ color: '#555b6e', fontSize: '11px', marginTop: '4px' }}>{sub}</div>
            </div>
          ))}
        </div>

        {/* Content */}
        {isLoading ? (
          <div style={{ color: '#555b6e', textAlign: 'center', padding: '64px' }}>Memuat signals…</div>
        ) : !signals || signals.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '64px 24px', background: '#141720', border: '1px solid #252836', borderRadius: '12px' }}>
            <div style={{ color: '#e8eaf0', fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>Belum ada signal</div>
            <div style={{ color: '#8b90a0', fontSize: '13px' }}>
              Signal muncul saat token memenuhi threshold momentum setelah scan berjalan.
            </div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 360px' : '1fr', gap: '16px', alignItems: 'start' }}>
            {/* Table */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h2 style={{ fontWeight: 600, fontSize: '15px', color: '#e8eaf0', margin: 0 }}>Signal History</h2>
                <span style={{ color: '#555b6e', fontSize: '12px' }}>{signals.length} signal</span>
              </div>

              <div style={{ background: '#141720', border: '1px solid #252836', borderRadius: '12px', overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: '#1c1f2e' }}>
                      {['Waktu', 'Token', 'Score', 'Entry Price', 'Status'].map((h) => (
                        <th key={h} style={{ padding: '10px 16px', textAlign: 'left', color: '#555b6e', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.6px' }}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {signals.map((sig, i) => {
                      const sb = scoreBadge(sig.score);
                      const stb = statusBadge(sig.status);
                      const isActive = selected?.id === sig.id;
                      return (
                        <tr
                          key={sig.id}
                          onClick={() => setSelected(isActive ? null : sig)}
                          style={{ background: isActive ? '#1a2035' : i % 2 === 0 ? '#141720' : '#131620', cursor: 'pointer', borderTop: '1px solid #1c1f2e', transition: 'background 0.15s' }}
                          onMouseEnter={(e) => { if (!isActive) (e.currentTarget as HTMLTableRowElement).style.background = '#1c1f2e'; }}
                          onMouseLeave={(e) => { if (!isActive) (e.currentTarget as HTMLTableRowElement).style.background = i % 2 === 0 ? '#141720' : '#131620'; }}
                        >
                          <td style={{ padding: '12px 16px', color: '#8b90a0', fontSize: '12px', whiteSpace: 'nowrap' }}>
                            {fmtDate(sig.created_at)}
                          </td>
                          <td style={{ padding: '12px 16px' }}>
                            <div style={{ fontWeight: 600, color: '#e8eaf0', fontSize: '13px' }}>
                              {sig.symbol ?? shortAddr(sig.address)}
                            </div>
                            <div style={{ color: '#555b6e', fontSize: '11px', marginTop: '2px' }}>
                              {sig.chain.toUpperCase()}
                            </div>
                          </td>
                          <td style={{ padding: '12px 16px' }}>
                            <span style={{ background: sb.bg, color: sb.text, padding: '3px 8px', borderRadius: '5px', fontSize: '12px', fontWeight: 700 }}>
                              {sig.score}
                            </span>
                          </td>
                          <td style={{ padding: '12px 16px', color: '#8b90a0', fontSize: '12px' }}>
                            {sig.entry_price_usd != null ? `$${sig.entry_price_usd.toFixed(6)}` : '—'}
                          </td>
                          <td style={{ padding: '12px 16px' }}>
                            <span style={{ background: stb.bg, color: stb.text, padding: '2px 7px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>
                              {sig.status}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <div style={{ marginTop: '10px', color: '#555b6e', fontSize: '11px' }}>
                Refresh otomatis 30 detik · Outcome dihitung setelah sinyal dicatat · Skor bukan prediksi pump
              </div>
            </div>

            {/* Detail panel */}
            {selected && <SignalDetailPanel signal={selected} />}
          </div>
        )}
      </div>
    </div>
  );
}

