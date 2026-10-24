'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import Link from 'next/link';

const API_BASE = '/api/v1';

interface Signal {
  id: number;
  created_at: string;
  score: number;
  status: string;
  entry_price_usd: number;
  chain: string;
  address: string;
  symbol?: string;
  name?: string;
}

async function fetchSignals(): Promise<Signal[]> {
  const res = await fetch(`${API_BASE}/signals?limit=100`);
  if (!res.ok) throw new Error('Failed to fetch signals');
  return res.json();
}

async function fetchProviderHealth(): Promise<{ status: string; provider: string }> {
  const res = await fetch(`${API_BASE}/providers/health`);
  if (!res.ok) throw new Error('Failed to fetch provider health');
  return res.json();
}

export default function SignalsPage() {
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);

  const { data: signals, isLoading } = useQuery({
    queryKey: ['signals'],
    queryFn: fetchSignals,
    refetchInterval: 30000,
  });

  const { data: providerHealth } = useQuery({
    queryKey: ['providerHealth'],
    queryFn: fetchProviderHealth,
    refetchInterval: 60000,
  });

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 65) return 'text-blue-600 bg-blue-100';
    return 'text-gray-600 bg-gray-100';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'High Momentum';
    if (score >= 65) return 'Watchlist';
    return 'Below Threshold';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">PumpWatch</h1>
              <p className="text-sm text-gray-600">Signal History</p>
            </div>
            <div className="flex gap-4">
              <Link href="/" className="text-blue-600 hover:underline">
                Watchlist
              </Link>
              <Link href="/signals" className="text-blue-600 font-semibold hover:underline">
                Signals
              </Link>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        <div className="mb-6 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-semibold">Signal History</h2>
            <p className="text-sm text-gray-600 mt-1">
              {signals ? `${signals.length} signals recorded` : 'Loading...'}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm">
              <span className="text-gray-600">Provider Status:</span>
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

        {isLoading ? (
          <div className="text-center py-12">Loading signals...</div>
        ) : !signals || signals.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg">
            <p className="text-gray-600">No signals recorded yet</p>
            <p className="text-sm text-gray-500 mt-2">
              Signals will appear here when tokens meet momentum threshold
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Time
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Token
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Score
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Entry Price
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {signals?.map((signal) => (
                      <tr
                        key={signal.id}
                        className="hover:bg-gray-50 cursor-pointer"
                        onClick={() => setSelectedSignal(signal)}
                      >
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                          {new Date(signal.created_at).toLocaleString()}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="font-medium text-gray-900">
                            {signal.symbol || signal.address.slice(0, 8)}
                          </div>
                          <div className="text-xs text-gray-500">{signal.chain.toUpperCase()}</div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className={`px-2 py-1 rounded text-sm font-medium ${getScoreColor(signal.score)}`}>
                            {signal.score}
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                          ${signal.entry_price_usd?.toFixed(6) || 'N/A'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span
                            className={`px-2 py-1 rounded text-xs ${
                              signal.status === 'active'
                                ? 'text-green-600 bg-green-100'
                                : 'text-gray-600 bg-gray-100'
                            }`}
                          >
                            {signal.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="lg:col-span-1">
              {selectedSignal ? (
                <SignalDetail signal={selectedSignal} />
              ) : (
                <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
                  Select a signal to view details
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function SignalDetail({ signal }: { signal: Signal }) {
  const { data: outcome } = useQuery({
    queryKey: ['outcome', signal.id],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/signals/${signal.id}/outcome`);
      if (res.status === 404) return null;
      if (!res.ok) throw new Error('Failed to fetch outcome');
      return res.json();
    },
    enabled: !!signal.id,
  });

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Signal #{signal.id}</h3>
      <div className="space-y-3 text-sm">
        <div>
          <span className="text-gray-600">Token:</span>
          <span className="ml-2 font-medium">{signal.symbol || signal.address.slice(0, 12)}</span>
        </div>
        <div>
          <span className="text-gray-600">Chain:</span>
          <span className="ml-2">{signal.chain.toUpperCase()}</span>
        </div>
        <div>
          <span className="text-gray-600">Entry Price:</span>
          <span className="ml-2">${signal.entry_price_usd?.toFixed(6) || 'N/A'}</span>
        </div>
        <div>
          <span className="text-gray-600">Created:</span>
          <span className="ml-2">{new Date(signal.created_at).toLocaleString()}</span>
        </div>

        {outcome && (
          <div className="mt-4 pt-4 border-t">
            <h4 className="font-medium mb-3">Outcomes</h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {outcome.return_5m !== null && (
                <div className="bg-gray-50 p-2 rounded">
                  <div className="text-gray-500">5m Return</div>
                  <div className={outcome.return_5m >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {(outcome.return_5m * 100).toFixed(2)}%
                  </div>
                </div>
              )}
              {outcome.return_1h !== null && (
                <div className="bg-gray-50 p-2 rounded">
                  <div className="text-gray-500">1h Return</div>
                  <div className={outcome.return_1h >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {(outcome.return_1h * 100).toFixed(2)}%
                  </div>
                </div>
              )}
              {outcome.return_24h !== null && (
                <div className="bg-gray-50 p-2 rounded">
                  <div className="text-gray-500">24h Return</div>
                  <div className={outcome.return_24h >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {(outcome.return_24h * 100).toFixed(2)}%
                  </div>
                </div>
              )}
              {outcome.mfe !== null && (
                <div className="bg-gray-50 p-2 rounded">
                  <div className="text-gray-500">MFE (Max Favorable)</div>
                  <div className="text-green-600">{(outcome.mfe * 100).toFixed(2)}%</div>
                </div>
              )}
              {outcome.mae !== null && (
                <div className="bg-gray-50 p-2 rounded">
                  <div className="text-gray-500">MAE (Max Adverse)</div>
                  <div className="text-red-600">{(outcome.mae * 100).toFixed(2)}%</div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
