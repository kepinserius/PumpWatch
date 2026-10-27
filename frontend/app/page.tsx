'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

// ── Types ────────────────────────────────────────────────────────────────────
interface Token {
  chain: string;
  address: string;
  symbol?: string;
  name?: string;
  last_seen?: string;
  snapshot_count: number;
}

interface ScoreComponent {
  name: string;
  score: number;
  weight: number;
}

interface RiskFlag {
  name: string;
  status: 'pass' | 'fail' | 'unknown';
  severity: string;
  reason: string;
}

interface TokenScore {
  token: { chain: string; address: string };
  risk: {
    level: string;
    hard_block: boolean;
    flags: RiskFlag[];
    coverage: number;
  };
  momentum: {
    score: number;
    components: ScoreComponent[];
    data_coverage: number;
  };
}

interface MarketSnapshot {
  id: number;
  observed_at: string;
  price_usd: string;
  liquidity_usd: string;
  volume_24h: string;
}

interface ProviderHealth {
  status: string;
  provider: string;
}

// ── API ──────────────────────────────────────────────────────────────────────
const API_BASE = '/api/v1';

const fetchJson = async <T,>(url: string): Promise<T> => {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
};

// ── Helpers ──────────────────────────────────────────────────────────────────
const shortAddr = (addr: string, n = 6) =>
  `${addr.slice(0, n)}…${addr.slice(-4)}`;

const fmtDate = (iso?: string) => {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleString('id-ID', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const scoreColor = (s: number) => {
  if (s >= 80) return '#22c55e';
  if (s >= 65) return '#4f8ef7';
  if (s >= 40) return '#f59e0b';
  return '#555b6e';
};

const riskBadge = (level: string, hardBlock: boolean) => {
  if (hardBlock) return { label: 'BLOCKED', bg: '#3b1a1a', text: '#ef4444', dot: '#ef4444' };
  if (level === 'low') return { label: 'LOW RISK', bg: '#0f2a1a', text: '#22c55e', dot: '#22c55e' };
  if (level === 'medium') return { label: 'MEDIUM RISK', bg: '#2a1f0a', text: '#f59e0b', dot: '#f59e0b' };
  return { label: 'HIGH RISK', bg: '#2a0f0f', text: '#ef4444', dot: '#ef4444' };
};

const flagStyle = (status: string) => {
  if (status === 'pass') return { bg: '#0f2a1a', text: '#22c55e', icon: '✓' };
  if (status === 'fail') return { bg: '#2a0f0f', text: '#ef4444', icon: '✕' };
  return { bg: '#1c1c28', text: '#8b90a0', icon: '?' };
};

// ── Sub-components ───────────────────────────────────────────────────────────
function NavBar({ providerHealth }: { providerHealth?: ProviderHealth }) {
  const isHealthy = providerHealth?.status === 'healthy';
  return (
    <nav
      style={{
        background: '#141720',
        borderBottom: '1px solid #252836',
        padding: '0 24px',
        height: '56px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ fontSize: '18px', fontWeight: 700, color: '#e8eaf0', letterSpacing: '-0.3px' }}>
          PumpWatch
        </span>
        <span
          style={{
            fontSize: '11px',
            color: '#555b6e',
            background: '#1c1f2e',
            padding: '2px 8px',
            borderRadius: '4px',
            fontWeight: 500,
          }}
        >
          SOLANA
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <Link
          href="/"
          style={{
            color: '#e8eaf0',
            textDecoration: 'none',
            fontSize: '13px',
            fontWeight: 600,
            borderBottom: '2px solid #4f8ef7',
            paddingBottom: '2px',
          }}
        >
          Watchlist
        </Link>
        <Link
          href="/signals"
          style={{ color: '#8b90a0', textDecoration: 'none', fontSize: '13px', fontWeight: 500 }}
        >
          Signals
        </Link>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: '#1c1f2e',
            padding: '4px 10px',
            borderRadius: '6px',
            fontSize: '12px',
          }}
        >
          <span
            style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              background: isHealthy ? '#22c55e' : '#f59e0b',
              display: 'inline-block',
            }}
          />
          <span style={{ color: '#8b90a0' }}>
            {providerHealth?.provider ?? 'Provider'}
          </span>
          <span style={{ color: isHealthy ? '#22c55e' : '#f59e0b', fontWeight: 600 }}>
            {providerHealth?.status ?? '…'}
          </span>
        </div>
      </div>
    </nav>
  );
}

function StatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <div
      style={{
        background: '#141720',
        border: '1px solid #252836',
        borderRadius: '10px',
        padding: '16px 20px',
      }}
    >
      <div style={{ color: '#555b6e', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '8px' }}>
        {label}
      </div>
      <div style={{ color: '#e8eaf0', fontSize: '22px', fontWeight: 700 }}>{value}</div>
      {sub && <div style={{ color: '#555b6e', fontSize: '11px', marginTop: '4px' }}>{sub}</div>}
    </div>
  );
}

function EmptyState() {
  return (
    <div
      style={{
        textAlign: 'center',
        padding: '64px 24px',
        background: '#141720',
        border: '1px solid #252836',
        borderRadius: '12px',
      }}
    >
      <div style={{ fontSize: '40px', marginBottom: '16px' }}>📡</div>
      <div style={{ color: '#e8eaf0', fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>
        Watchlist kosong
      </div>
      <div style={{ color: '#8b90a0', fontSize: '13px', lineHeight: '1.6', maxWidth: '360px', margin: '0 auto 20px' }}>
        Database belum berisi token. Jalankan scan pertama untuk mulai menemukan token Solana.
      </div>
      <code
        style={{
          display: 'inline-block',
          background: '#1c1f2e',
          border: '1px solid #252836',
          color: '#4f8ef7',
          padding: '8px 16px',
          borderRadius: '6px',
          fontSize: '12px',
          fontFamily: 'monospace',
        }}
      >
        POST /api/v1/admin/scan
      </code>
      <div style={{ color: '#555b6e', fontSize: '11px', marginTop: '12px' }}>
        Gunakan header <code style={{ color: '#8b90a0' }}>api_key</code> yang sesuai dengan config
      </div>
    </div>
  );
}

function ScoreBar({ score, label }: { score: number; label: string }) {
  const pct = Math.max(0, Math.min(100, score));
  const color = scoreColor(pct);
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
        <span style={{ color: '#8b90a0', fontSize: '12px' }}>{label}</span>
        <span style={{ color, fontWeight: 700, fontSize: '14px' }}>{pct}</span>
      </div>
      <div style={{ height: '4px', background: '#252836', borderRadius: '2px', overflow: 'hidden' }}>
        <div
          style={{
            height: '100%',
            width: `${pct}%`,
            background: color,
            borderRadius: '2px',
            transition: 'width 0.4s ease',
          }}
        />
      </div>
    </div>
  );
}

function TokenDetailPanel({ token }: { token: Token }) {
  const { data: score, isLoading: scoreLoading } = useQuery({
    queryKey: ['score', token.chain, token.address],
    queryFn: () => fetchJson<TokenScore>(`${API_BASE}/tokens/${token.chain}/${token.address}/score`),
  });

  const { data: snapshots } = useQuery({
    queryKey: ['snapshots', token.chain, token.address],
    queryFn: () => fetchJson<MarketSnapshot[]>(`${API_BASE}/tokens/${token.chain}/${token.address}/snapshots`),
  });

  const risk = score?.risk;
  const momentum = score?.momentum;
  const badge = risk ? riskBadge(risk.level, risk.hard_block) : null;

  const chartData = (snapshots ?? []).slice(-20).map((s) => ({
    t: new Date(s.observed_at).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }),
    price: parseFloat(s.price_usd) || 0,
  }));

  return (
    <div
      style={{
        background: '#141720',
        border: '1px solid #252836',
        borderRadius: '12px',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid #252836',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
        }}
      >
        <div>
          <div style={{ fontWeight: 700, fontSize: '16px', color: '#e8eaf0' }}>
            {token.symbol ?? shortAddr(token.address)}
          </div>
          {token.name && (
            <div style={{ color: '#8b90a0', fontSize: '12px', marginTop: '2px' }}>{token.name}</div>
          )}
        </div>
        {badge && (
          <div
            style={{
              background: badge.bg,
              color: badge.text,
              padding: '3px 8px',
              borderRadius: '5px',
              fontSize: '10px',
              fontWeight: 700,
              letterSpacing: '0.5px',
            }}
          >
            {badge.label}
          </div>
        )}
      </div>

      <div style={{ padding: '20px' }}>
        {scoreLoading ? (
          <div style={{ color: '#555b6e', textAlign: 'center', padding: '24px' }}>Memuat skor…</div>
        ) : score ? (
          <>
            {/* Momentum Score */}
            <div style={{ marginBottom: '20px' }}>
              <div
                style={{
                  color: '#555b6e',
                  fontSize: '11px',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.6px',
                  marginBottom: '12px',
                }}
              >
                Momentum Score
              </div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '16px',
                  marginBottom: '12px',
                }}
              >
                <div
                  style={{
                    fontSize: '40px',
                    fontWeight: 800,
                    color: scoreColor(momentum!.score),
                    lineHeight: 1,
                  }}
                >
                  {momentum!.score}
                </div>
                <div>
                  <div style={{ color: '#8b90a0', fontSize: '12px' }}>
                    {momentum!.score >= 80
                      ? 'Momentum tinggi — review risiko'
                      : momentum!.score >= 65
                        ? 'Watchlist'
                        : 'Di bawah threshold'}
                  </div>
                  <div style={{ color: '#555b6e', fontSize: '11px', marginTop: '2px' }}>
                    Data coverage {(momentum!.data_coverage * 100).toFixed(0)}%
                  </div>
                </div>
              </div>

              {/* Score components */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {momentum!.components.map((c) => (
                  <ScoreBar
                    key={c.name}
                    label={c.name.replace(/_/g, ' ')}
                    score={Math.round(c.score * 100)}
                  />
                ))}
              </div>
            </div>

            {/* Risk Flags */}
            {risk!.flags.length > 0 && (
              <div style={{ marginBottom: '20px' }}>
                <div
                  style={{
                    color: '#555b6e',
                    fontSize: '11px',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    letterSpacing: '0.6px',
                    marginBottom: '10px',
                  }}
                >
                  Risk Flags — coverage {(risk!.coverage * 100).toFixed(0)}%
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {risk!.flags.map((f, i) => {
                    const s = flagStyle(f.status);
                    return (
                      <div
                        key={i}
                        style={{
                          background: s.bg,
                          borderRadius: '6px',
                          padding: '8px 12px',
                          display: 'flex',
                          gap: '8px',
                          alignItems: 'flex-start',
                        }}
                      >
                        <span style={{ color: s.text, fontWeight: 700, fontSize: '12px', flexShrink: 0, marginTop: '1px' }}>
                          {s.icon}
                        </span>
                        <div>
                          <div style={{ color: s.text, fontWeight: 600, fontSize: '12px' }}>
                            {f.name.replace(/_/g, ' ')}
                          </div>
                          <div style={{ color: '#8b90a0', fontSize: '11px', marginTop: '2px', lineHeight: '1.4' }}>
                            {f.reason}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Price chart */}
            {chartData.length > 1 && (
              <div>
                <div
                  style={{
                    color: '#555b6e',
                    fontSize: '11px',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    letterSpacing: '0.6px',
                    marginBottom: '10px',
                  }}
                >
                  Harga ({chartData.length} snapshot terakhir)
                </div>
                <div style={{ height: '120px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#252836" />
                      <XAxis dataKey="t" hide />
                      <YAxis domain={['auto', 'auto']} hide />
                      <Tooltip
                        contentStyle={{
                          background: '#1c1f2e',
                          border: '1px solid #252836',
                          borderRadius: '6px',
                          color: '#e8eaf0',
                          fontSize: '12px',
                        }}
                        formatter={(v: number) => [`$${v.toFixed(8)}`, 'Price']}
                      />
                      <Line
                        type="monotone"
                        dataKey="price"
                        stroke="#4f8ef7"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Disclaimer */}
            <div
              style={{
                marginTop: '16px',
                padding: '10px 12px',
                background: '#1c1f2e',
                borderRadius: '6px',
                fontSize: '11px',
                color: '#555b6e',
                lineHeight: '1.5',
              }}
            >
              ⚠️ Skor bukan probabilitas pump. Skor adalah ringkasan momentum berbasis rule — bukan rekomendasi beli.
            </div>
          </>
        ) : (
          <div style={{ color: '#555b6e', textAlign: 'center', padding: '24px' }}>
            Gagal memuat data skor
          </div>
        )}

        {/* Address */}
        <div
          style={{
            marginTop: '16px',
            paddingTop: '16px',
            borderTop: '1px solid #252836',
            color: '#555b6e',
            fontSize: '11px',
          }}
        >
          <div style={{ marginBottom: '4px' }}>
            <span style={{ color: '#8b90a0' }}>Chain: </span>
            {token.chain.toUpperCase()}
          </div>
          <div style={{ wordBreak: 'break-all' }}>
            <span style={{ color: '#8b90a0' }}>Address: </span>
            {token.address}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function Home() {
  const [selected, setSelected] = useState<Token | null>(null);

  const { data: tokens, isLoading, error } = useQuery({
    queryKey: ['tokens'],
    queryFn: () => fetchJson<Token[]>(`${API_BASE}/tokens?limit=50`),
    refetchInterval: 30000,
  });

  const { data: providerHealth } = useQuery({
    queryKey: ['providerHealth'],
    queryFn: () => fetchJson<ProviderHealth>(`${API_BASE}/providers/health`),
    refetchInterval: 60000,
  });

  const totalSnapshots = tokens?.reduce((sum, t) => sum + t.snapshot_count, 0) ?? 0;

  return (
    <div style={{ minHeight: '100vh', background: '#0d0f14' }}>
      <NavBar providerHealth={providerHealth} />

      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '24px' }}>
        {/* Stat bar */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
            gap: '12px',
            marginBottom: '24px',
          }}
        >
          <StatCard label="Tokens Tracked" value={tokens?.length ?? '—'} sub="dari scan terakhir" />
          <StatCard label="Total Snapshots" value={totalSnapshots} sub="data pasar tersimpan" />
          <StatCard
            label="Last Update"
            value={
              tokens?.[0]?.last_seen
                ? fmtDate(tokens[0].last_seen)
                : '—'
            }
            sub="snapshot terbaru"
          />
          <StatCard
            label="Data Provider"
            value={providerHealth?.status ?? '—'}
            sub={providerHealth?.provider ?? ''}
          />
        </div>

        {/* Content */}
        {error ? (
          <div
            style={{
              padding: '24px',
              background: '#2a0f0f',
              border: '1px solid #3b1a1a',
              borderRadius: '10px',
              color: '#ef4444',
              fontSize: '13px',
            }}
          >
            ✕ Gagal memuat token — pastikan backend berjalan di localhost:8000
          </div>
        ) : isLoading ? (
          <div style={{ color: '#555b6e', textAlign: 'center', padding: '64px' }}>
            Memuat data…
          </div>
        ) : !tokens || tokens.length === 0 ? (
          <EmptyState />
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: selected ? '1fr 360px' : '1fr',
              gap: '16px',
              alignItems: 'start',
            }}
          >
            {/* Token table */}
            <div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '12px',
                }}
              >
                <h2 style={{ fontWeight: 600, fontSize: '15px', color: '#e8eaf0', margin: 0 }}>
                  Watchlist
                </h2>
                <span style={{ color: '#555b6e', fontSize: '12px' }}>
                  {tokens.length} token
                </span>
              </div>

              <div
                style={{
                  background: '#141720',
                  border: '1px solid #252836',
                  borderRadius: '12px',
                  overflow: 'hidden',
                }}
              >
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: '#1c1f2e' }}>
                      {['Token', 'Chain', 'Last Update', 'Snapshots'].map((h) => (
                        <th
                          key={h}
                          style={{
                            padding: '10px 16px',
                            textAlign: 'left',
                            color: '#555b6e',
                            fontSize: '11px',
                            fontWeight: 600,
                            textTransform: 'uppercase',
                            letterSpacing: '0.6px',
                          }}
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {tokens.map((t, i) => {
                      const isActive = selected?.address === t.address;
                      return (
                        <tr
                          key={`${t.chain}/${t.address}`}
                          onClick={() => setSelected(isActive ? null : t)}
                          style={{
                            background: isActive ? '#1a2035' : i % 2 === 0 ? '#141720' : '#131620',
                            cursor: 'pointer',
                            borderTop: '1px solid #1c1f2e',
                            transition: 'background 0.15s',
                          }}
                          onMouseEnter={(e) => {
                            if (!isActive) (e.currentTarget as HTMLTableRowElement).style.background = '#1c1f2e';
                          }}
                          onMouseLeave={(e) => {
                            if (!isActive)
                              (e.currentTarget as HTMLTableRowElement).style.background =
                                i % 2 === 0 ? '#141720' : '#131620';
                          }}
                        >
                          <td style={{ padding: '12px 16px' }}>
                            <div style={{ fontWeight: 600, color: '#e8eaf0', fontSize: '13px' }}>
                              {t.symbol ?? shortAddr(t.address)}
                            </div>
                            {t.name && (
                              <div style={{ color: '#555b6e', fontSize: '11px', marginTop: '2px' }}>
                                {t.name}
                              </div>
                            )}
                          </td>
                          <td style={{ padding: '12px 16px' }}>
                            <span
                              style={{
                                background: '#1c1f2e',
                                color: '#8b90a0',
                                padding: '2px 7px',
                                borderRadius: '4px',
                                fontSize: '11px',
                                fontWeight: 600,
                              }}
                            >
                              {t.chain.toUpperCase()}
                            </span>
                          </td>
                          <td style={{ padding: '12px 16px', color: '#8b90a0', fontSize: '12px' }}>
                            {fmtDate(t.last_seen)}
                          </td>
                          <td style={{ padding: '12px 16px', color: '#8b90a0', fontSize: '12px' }}>
                            {t.snapshot_count}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Stale data note */}
              <div style={{ marginTop: '10px', color: '#555b6e', fontSize: '11px' }}>
                Data di-refresh setiap 30 detik · Sumber: DexScreener · Skor dihitung live dari backend
              </div>
            </div>

            {/* Detail panel */}
            {selected && <TokenDetailPanel token={selected} />}
          </div>
        )}
      </div>
    </div>
  );
}


