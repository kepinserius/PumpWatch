'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface Token {
  chain: string;
  address: string;
  symbol?: string;
  name?: string;
  last_seen?: string;
  snapshot_count: number;
}

interface TokenScore {
  token: { chain: string; address: string };
  risk: {
    level: string;
    hard_block: boolean;
    flags: Array<{ name: string; status: string; severity: string; reason: string }>;
    coverage: number;
  };
  momentum: {
    score: number;
    components: Array<{ name: string; score: number; weight: number }>;
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

const API_BASE = '/api/v1';

async function fetchTokens(): Promise<Token[]> {
  const res = await fetch(`${API_BASE}/tokens?limit=50`);
  if (!res.ok) throw new Error('Failed to fetch tokens');
  return res.json();
}

async function fetchTokenScore(chain: string, address: string): Promise<TokenScore> {
  const res = await fetch(`${API_BASE}/tokens/${chain}/${address}/score`);
  if (!res.ok) throw new Error('Failed to fetch score');
  return res.json();
}

async function fetchSnapshots(chain: string, address: string): Promise<MarketSnapshot[]> {
  const res = await fetch(`${API_BASE}/tokens/${chain}/${address}/snapshots`);
  if (!res.ok) throw new Error('Failed to fetch snapshots');
  return res.json();
}

async function fetchProviderHealth(): Promise<{ status: string; provider: string }> {
  const res = await fetch(`${API_BASE}/providers/health`);
  if (!res.ok) throw new Error('Failed to fetch provider health');
  return res.json();
}

export default function Home() {
  const [selectedToken, setSelectedToken] = useState<Token | null>(null);

  const { data: tokens, isLoading: tokensLoading, error: tokensError } = useQuery({
    queryKey: ['tokens'],
    queryFn: fetchTokens,
    refetchInterval: 30000,
  });

  const { data: providerHealth } = useQuery({
    queryKey: ['providerHealth'],
    queryFn: fetchProviderHealth,
    refetchInterval: 60000,
  });

  const { data: score } = useQuery({
    queryKey: ['score', selectedToken?.chain, selectedToken?.address],
    queryFn: () => fetchTokenScore(selectedToken!.chain, selectedToken!.address),
    enabled: !!selectedToken,
  });

  const { data: snapshots } = useQuery({
    queryKey: ['snapshots', selectedToken?.chain, selectedToken?.address],
    queryFn: () => fetchSnapshots(selectedToken!.chain, selectedToken!.address),
    enabled: !!selectedToken,
  });

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 65) return 'text-blue-600';
    return 'text-gray-600';
  };

  const getRiskColor = (level: string) => {
    if (level === 'low') return 'text-green-600 bg-green-100';
    if (level === 'medium') return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">PumpWatch</h1>
              <p className="text-sm text-gray-600">Memecoin Momentum & Risk Scanner</p>
            </div>
            <div className="flex gap-4 items-center">
              <Link href="/signals" className="text-blue-600 hover:underline">
                Signal History
              </Link>
              <div className="text-sm">
                <span className="text-gray-600">Provider:</span>
                <span
                  className={`ml-2 px-2 py-1 rounded ${
                    providerHealth?.status === 'healthy'
                      ? 'text-green-600 bg-green-100'
                      : 'text-yellow-600 bg-yellow-100'
                  }`}
                >
                  {providerHealth?.status || 'Unknown'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        {tokensError ? (
          <div className="text-center py-12 bg-red-50 rounded-lg">
            <p className="text-red-600">Failed to load tokens. Please check backend connection.</p>
          </div>
        ) : tokensLoading ? (
          <div className="text-center py-12">Loading tokens...</div>
        ) : !tokens || tokens.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg">
            <p className="text-gray-600">No tokens in watchlist yet</p>
            <p className="text-sm text-gray-500 mt-2">
              Run a scan to discover tokens: POST /api/v1/admin/scan
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold">Watchlist</h2>
                <span className="text-sm text-gray-600">{tokens.length} tokens</span>
              </div>
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Token</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Chain</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Updated</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Snapshots</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {tokens.map((token) => (
                      <tr
                        key={`${token.chain}/${token.address}`}
                        className={`hover:bg-gray-50 cursor-pointer ${
                          selectedToken?.address === token.address ? 'bg-blue-50' : ''
                        }`}
                        onClick={() => setSelectedToken(token)}
                      >
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="font-medium text-gray-900">
                            {token.symbol || token.address.slice(0, 8)}
                          </div>
                          {token.name && <div className="text-sm text-gray-500">{token.name}</div>}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-gray-600">{token.chain.toUpperCase()}</td>
                        <td className="px-4 py-3 whitespace-nowrap text-gray-600">
                          {token.last_seen ? new Date(token.last_seen).toLocaleString() : 'N/A'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-gray-600">{token.snapshot_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="lg:col-span-1">
              {selectedToken && score ? (
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-xl font-semibold mb-4">
                    {selectedToken.symbol || 'Token Details'}
                  </h2>

                  <div className="mb-6">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-600">Momentum Score</span>
                      <span className={`text-2xl font-bold ${getScoreColor(score.momentum.score)}`}>
                        {score.momentum.score}
                      </span>
                    </div>
                    <div className="text-sm text-gray-500">
                      Data Coverage: {(score.momentum.data_coverage * 100).toFixed(0)}%
                    </div>
                  </div>

                  <div className="mb-6">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-600">Risk Level</span>
                      <span className={`px-2 py-1 rounded text-sm font-medium ${getRiskColor(score.risk.level)}`}>
                        {score.risk.level.toUpperCase()}
                      </span>
                    </div>
                    {score.risk.hard_block && (
                      <div className="text-sm text-red-600 font-medium">⚠️ Hard Blocked</div>
                    )}
                  </div>

                  {score.momentum.components.length > 0 && (
                    <div className="mb-6">
                      <h3 className="font-medium mb-2">Score Components</h3>
                      <div className="space-y-2">
                        {score.momentum.components.map((comp) => (
                          <div key={comp.name} className="flex justify-between text-sm">
                            <span className="text-gray-600">{comp.name.replace('_', ' ')}</span>
                            <span className="font-medium">{(comp.score * 100).toFixed(0)}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {score.risk.flags.length > 0 && (
                    <div className="mb-6">
                      <h3 className="font-medium mb-2">Risk Flags</h3>
                      <div className="space-y-1 text-sm">
                        {score.risk.flags.map((flag, i) => (
                          <div
                            key={i}
                            className={`px-2 py-1 rounded ${
                              flag.status === 'pass'
                                ? 'text-green-600 bg-green-50'
                                : flag.status === 'fail'
                                  ? 'text-red-600 bg-red-50'
                                  : 'text-gray-600 bg-gray-50'
                            }`}
                          >
                            <span className="font-medium">{flag.status.toUpperCase()}</span> - {flag.reason}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {snapshots && snapshots.length > 0 && (
                    <div>
                      <h3 className="font-medium mb-2">Price History (last {snapshots.length})</h3>
                      <div className="h-48">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={snapshots.slice(-20).map(s => ({
                            ...s,
                            price: parseFloat(s.price_usd)
                          }))}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                            <XAxis dataKey="observed_at" hide />
                            <YAxis domain={['auto', 'auto']} hide />
                            <Tooltip
                              contentStyle={{ backgroundColor: '#fff', borderRadius: '8px' }}
                              itemStyle={{ color: '#3b82f6' }}
                              formatter={(value: number) => [`$${value.toFixed(6)}`, 'Price']}
                            />
                            <Line type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={2} dot={false} />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}

                  <div className="mt-6 pt-4 border-t text-xs text-gray-500">
                    <div>Chain: {selectedToken.chain.toUpperCase()}</div>
                    <div className="break-all">Address: {selectedToken.address}</div>
                  </div>
                </div>
              ) : selectedToken ? (
                <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
                  Loading token details...
                </div>
              ) : (
                <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
                  Select a token to view details
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
