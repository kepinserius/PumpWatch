'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface MarketSnapshot {
  id: number;
  observed_at: string;
  price_usd: string;
  liquidity_usd: string;
  volume_24h: string;
}

interface Token {
  chain: string;
  address: string;
  symbol?: string;
  name?: string;
  last_seen?: string;
  snapshot_count: number;
}

const API_BASE = '/api/v1';

async function fetchTokens(): Promise<Token[]> {
  const res = await fetch(`${API_BASE}/tokens?limit=50`);
  if (!res.ok) throw new Error('Failed to fetch tokens');
  return res.json();
}

async function fetchSnapshots(chain: string, address: string): Promise<MarketSnapshot[]> {
  const res = await fetch(`${API_BASE}/tokens/${chain}/${address}/snapshots`);
  if (!res.ok) throw new Error('Failed to fetch snapshots');
  return res.json();
}

export default function Home() {
  const [selectedToken, setSelectedToken] = useState<Token | null>(null);

  const { data: tokens, isLoading } = useQuery({
    queryKey: ['tokens'],
    queryFn: fetchTokens,
  });

  const { data: snapshots } = useQuery({
    queryKey: ['snapshots', selectedToken?.chain, selectedToken?.address],
    queryFn: () => fetchSnapshots(selectedToken!.chain, selectedToken!.address),
    enabled: !!selectedToken,
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">PumpWatch</h1>
          <p className="text-sm text-gray-600">Memecoin Momentum & Risk Scanner</p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        {isLoading ? (
          <div className="text-center py-12">Loading tokens...</div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <h2 className="text-xl font-semibold mb-4">Watchlist</h2>
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left">Token</th>
                      <th className="px-4 py-3 text-left">Chain</th>
                      <th className="px-4 py-3 text-left">Last Updated</th>
                      <th className="px-4 py-3 text-left">Snapshots</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {tokens?.map((token) => (
                      <tr
                        key={`${token.chain}/${token.address}`}
                        className="hover:bg-gray-50 cursor-pointer"
                        onClick={() => setSelectedToken(token)}
                      >
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="font-medium text-gray-900">
                            {token.symbol || token.address.slice(0, 8)}
                          </div>
                          {token.name && (
                            <div className="text-sm text-gray-500">{token.name}</div>
                          )}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-gray-600">
                          {token.chain.toUpperCase()}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-gray-600">
                          {token.last_seen ? new Date(token.last_seen).toLocaleString() : 'N/A'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-gray-600">
                          {token.snapshot_count}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="lg:col-span-1">
              {selectedToken && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-xl font-semibold mb-4">
                    {selectedToken.symbol || 'Token Details'}
                  </h2>
                  <div className="space-y-2 text-sm">
                    <p>
                      <span className="font-medium">Chain:</span> {selectedToken.chain.toUpperCase()}
                    </p>
                    <p>
                      <span className="font-medium">Address:</span>{' '}
                      <code className="block break-all bg-gray-100 p-2 rounded">
                        {selectedToken.address}
                      </code>
                    </p>
                    {snapshots && snapshots.length > 0 && (
                      <div className="mt-4">
                        <h3 className="font-medium mb-2">Price History (last {snapshots.length})</h3>
                        <div className="h-48">
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={snapshots.slice(-20)}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                              <XAxis dataKey="observed_at" hide />
                              <YAxis domain={['auto', 'auto']} hide />
                              <Tooltip
                                contentStyle={{ backgroundColor: '#fff', borderRadius: '8px' }}
                                itemStyle={{ color: '#3b82f6' }}
                              />
                              <Line
                                type="monotone"
                                dataKey="price_usd"
                                stroke="#3b82f6"
                                strokeWidth={2}
                                dot={false}
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
