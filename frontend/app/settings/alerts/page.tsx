'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';

// ── Types ────────────────────────────────────────────────────────────────────
interface AlertRule {
  id: number;
  name: string;
  token_id: number | null;
  is_global: boolean;
  momentum_threshold: number | null;
  risk_level_max: string | null;
  min_liquidity_usd: number | null;
  cooldown_minutes: number;
  priority: 'low' | 'normal' | 'high';
  enabled: boolean;
  created_at: string;
}

interface AlertRuleForm {
  name: string;
  token_id: string | null;
  is_global: boolean;
  momentum_threshold: string;
  risk_level_max: string | null;
  min_liquidity_usd: string;
  cooldown_minutes: string;
  priority: 'low' | 'normal' | 'high';
  enabled: boolean;
}

const API_BASE = '/api/v1';

// ── API Functions ────────────────────────────────────────────────────────────
const fetchRules = async (): Promise<AlertRule[]> => {
  const res = await fetch(`${API_BASE}/alert-rules`);
  if (!res.ok) throw new Error('Failed to fetch rules');
  return res.json();
};

const createRule = async (rule: AlertRuleForm): Promise<AlertRule> => {
  const res = await fetch(`${API_BASE}/alert-rules`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(rule),
  });
  if (!res.ok) throw new Error('Failed to create rule');
  return res.json();
};

const updateRule = async (id: number, updates: Partial<AlertRuleForm>): Promise<void> => {
  const res = await fetch(`${API_BASE}/alert-rules/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error('Failed to update rule');
};

const deleteRule = async (id: number): Promise<void> => {
  const res = await fetch(`${API_BASE}/alert-rules/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete rule');
};

// ── UI Components ────────────────────────────────────────────────────────────
function NavBar() {
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
        <Link href="/" style={{ color: '#e8eaf0', textDecoration: 'none', fontSize: '18px', fontWeight: 700 }}>
          PumpWatch
        </Link>
        <span
          style={{
            fontSize: '11px',
            color: '#555b6e',
            background: '#1c1f2e',
            padding: '2px 8px',
            borderRadius: '4px',
          }}
        >
          SOLANA
        </span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <Link href="/" style={{ color: '#8b90a0', textDecoration: 'none', fontSize: '13px' }}>
          Watchlist
        </Link>
        <Link href="/signals" style={{ color: '#8b90a0', textDecoration: 'none', fontSize: '13px' }}>
          Signals
        </Link>
        <Link href="/analytics" style={{ color: '#8b90a0', textDecoration: 'none', fontSize: '13px' }}>
          Analytics
        </Link>
        <Link href="/backtest" style={{ color: '#8b90a0', textDecoration: 'none', fontSize: '13px' }}>
          Backtest
        </Link>
      </div>
    </nav>
  );
}

function PriorityBadge({ priority }: { priority: string }) {
  const colors = {
    high: { bg: '#2a0f0f', text: '#ef4444' },
    normal: { bg: '#1c1f2e', text: '#4f8ef7' },
    low: { bg: '#0f2a1a', text: '#22c55e' },
  };
  const style = colors[priority as keyof typeof colors] || colors.normal;

  return (
    <span
      style={{
        background: style.bg,
        color: style.text,
        padding: '2px 8px',
        borderRadius: '4px',
        fontSize: '11px',
        fontWeight: 500,
      }}
    >
      {priority.toUpperCase()}
    </span>
  );
}

function RuleStatus({ enabled }: { enabled: boolean }) {
  const style = enabled
    ? { bg: '#0f2a1a', text: '#22c55e', label: 'Active' }
    : { bg: '#2a0f0f', text: '#ef4444', label: 'Disabled' };

  return (
    <span
      style={{
        background: style.bg,
        color: style.text,
        padding: '2px 8px',
        borderRadius: '4px',
        fontSize: '11px',
      }}
    >
      {style.label}
    </span>
  );
}

function RuleForm({ initialData, onSubmit, onCancel }: { initialData?: AlertRule | null; onSubmit: (data: AlertRuleForm) => void; onCancel: () => void }) {
  const [form, setForm] = useState<AlertRuleForm>({
    name: initialData?.name || '',
    token_id: initialData?.token_id?.toString() || '',
    is_global: initialData?.is_global ?? true,
    momentum_threshold: initialData?.momentum_threshold?.toString() || '70',
    risk_level_max: initialData?.risk_level_max || 'medium',
    min_liquidity_usd: initialData?.min_liquidity_usd?.toString() || '',
    cooldown_minutes: initialData?.cooldown_minutes?.toString() || '60',
    priority: initialData?.priority || 'normal',
    enabled: initialData?.enabled ?? true,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      name: form.name,
      token_id: form.token_id ? parseInt(form.token_id) : null,
      is_global: form.is_global,
      momentum_threshold: form.momentum_threshold ? parseFloat(form.momentum_threshold) : null,
      risk_level_max: form.risk_level_max || null,
      min_liquidity_usd: form.min_liquidity_usd ? parseFloat(form.min_liquidity_usd) : null,
      cooldown_minutes: parseInt(form.cooldown_minutes),
      priority: form.priority,
      enabled: form.enabled,
    });
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div>
        <label style={{ display: 'block', marginBottom: '4px', color: '#8b90a0', fontSize: '12px' }}>Rule Name</label>
        <input
          type="text"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
          style={{
            width: '100%',
            padding: '8px 12px',
            background: '#1c1f2e',
            border: '1px solid #252836',
            borderRadius: '6px',
            color: '#e8eaf0',
            fontSize: '14px',
          }}
          placeholder="e.g., High Momentum Alert"
        />
      </div>

      <div style={{ display: 'flex', gap: '12px' }}>
        <div style={{ flex: 1 }}>
          <label style={{ display: 'block', marginBottom: '4px', color: '#8b90a0', fontSize: '12px' }}>Apply To</label>
          <select
            value={form.is_global ? 'global' : 'token'}
            onChange={(e) => setForm({ ...form, is_global: e.target.value === 'global' })}
            style={{
              width: '100%',
              padding: '8px 12px',
              background: '#1c1f2e',
              border: '1px solid #252836',
              borderRadius: '6px',
              color: '#e8eaf0',
              fontSize: '14px',
            }}
          >
            <option value="global">All Tokens (Global Rule)</option>
            <option value="token">Specific Token</option>
          </select>
        </div>

        {!form.is_global && (
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '4px', color: '#8b90a0', fontSize: '12px' }}>Token Address</label>
            <input
              type="text"
              value={form.token_id}
              onChange={(e) => setForm({ ...form, token_id: e.target.value })}
              placeholder="Enter token ID"
              style={{
                width: '100%',
                padding: '8px 12px',
                background: '#1c1f2e',
                border: '1px solid #252836',
                borderRadius: '6px',
                color: '#e8eaf0',
                fontSize: '14px',
              }}
            />
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: '12px' }}>
        <div style={{ flex: 1 }}>
          <label style={{ display: 'block', marginBottom: '4px', color: '#8b90a0', fontSize: '12px' }}>Min Momentum Score</label>
          <input
            type="number"
            value={form.momentum_threshold}
            onChange={(e) => setForm({ ...form, momentum_threshold: e.target.value })}
            min="0"
            max="100"
            style={{
              width: '100%',
              padding: '8px 12px',
              background: '#1c1f2e',
              border: '1px solid #252836',
              borderRadius: '6px',
              color: '#e8eaf0',
              fontSize: '14px',
            }}
          />
        </div>

        <div style={{ flex: 1 }}>
          <label style={{ display: 'block', marginBottom: '4px', color: '#8b90a0', fontSize: '12px' }}>Max Risk Level</label>
          <select
            value={form.risk_level_max || 'medium'}
            onChange={(e) => setForm({ ...form, risk_level_max: e.target.value })}
            style={{
              width: '100%',
              padding: '8px 12px',
              background: '#1c1f2e',
              border: '1px solid #252836',
              borderRadius: '6px',
              color: '#e8eaf0',
              fontSize: '14px',
            }}
          >
            <option value="low">Low Only</option>
            <option value="medium">Low + Medium</option>
            <option value="high">All</option>
          </select>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '12px' }}>
        <div style={{ flex: 1 }}>
          <label style={{ display: 'block', marginBottom: '4px', color: '#8b90a0', fontSize: '12px' }}>Cooldown (minutes)</label>
          <input
            type="number"
            value={form.cooldown_minutes}
            onChange={(e) => setForm({ ...form, cooldown_minutes: e.target.value })}
            min="1"
            max="1440"
            style={{
              width: '100%',
              padding: '8px 12px',
              background: '#1c1f2e',
              border: '1px solid #252836',
              borderRadius: '6px',
              color: '#e8eaf0',
              fontSize: '14px',
            }}
          />
        </div>

        <div style={{ flex: 1 }}>
          <label style={{ display: 'block', marginBottom: '4px', color: '#8b90a0', fontSize: '12px' }}>Priority</label>
          <select
            value={form.priority}
            onChange={(e) => setForm({ ...form, priority: e.target.value as 'low' | 'normal' | 'high' })}
            style={{
              width: '100%',
              padding: '8px 12px',
              background: '#1c1f2e',
              border: '1px solid #252836',
              borderRadius: '6px',
              color: '#e8eaf0',
              fontSize: '14px',
            }}
          >
            <option value="low">Low</option>
            <option value="normal">Normal</option>
            <option value="high">High</option>
          </select>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '12px' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#8b90a0', fontSize: '14px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={form.enabled}
            onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
            style={{
              width: '16px',
              height: '16px',
              accentColor: '#4f8ef7',
            }}
          />
          Enabled
        </label>

        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#8b90a0', fontSize: '14px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={form.is_global}
            onChange={(e) => setForm({ ...form, is_global: e.target.checked })}
            style={{
              width: '16px',
              height: '16px',
              accentColor: '#4f8ef7',
            }}
          />
          Apply to all tokens (global rule)
        </label>
      </div>

      <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
        <button
          type="submit"
          style={{
            flex: 1,
            padding: '10px 16px',
            background: '#4f8ef7',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          {initialData ? 'Update Rule' : 'Create Rule'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          style={{
            flex: 1,
            padding: '10px 16px',
            background: '#1c1f2e',
            color: '#8b90a0',
            border: '1px solid #252836',
            borderRadius: '6px',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

export default function AlertsPage() {
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null);

  const { data: rules, isLoading, error } = useQuery({
    queryKey: ['alert-rules'],
    queryFn: fetchRules,
  });

  const createMutation = useMutation({
    mutationFn: createRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] });
      setIsCreating(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: updateRule,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] });
      setEditingRule(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] });
    },
  });

  const handleCreate = (data: AlertRuleForm) => {
    createMutation.mutate(data);
  };

  const handleUpdate = (data: AlertRuleForm) => {
    if (editingRule) {
      updateMutation.mutate([editingRule.id, data]);
    }
  };

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this rule?')) {
      deleteMutation.mutate(id);
    }
  };

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', color: '#8b90a0' }}>
        Loading alert rules...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '48px', color: '#ef4444', textAlign: 'center' }}>
        Failed to load alert rules
      </div>
    );
  }

  return (
    <div style={{ background: '#0d0f14', minHeight: '100vh' }}>
      <NavBar />

      <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
          <h1 style={{ color: '#e8eaf0', fontSize: '24px', fontWeight: 700 }}>Alert Rules</h1>
          <button
            onClick={() => setIsCreating(true)}
            style={{
              padding: '10px 20px',
              background: '#4f8ef7',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            + Create New Rule
          </button>
        </div>

        {isCreating ? (
          <div style={{ background: '#141720', borderRadius: '12px', padding: '24px', marginBottom: '24px' }}>
            <h2 style={{ color: '#e8eaf0', fontSize: '18px', fontWeight: 600, marginBottom: '16px' }}>Create Alert Rule</h2>
            <RuleForm onSubmit={handleCreate} onCancel={() => setIsCreating(false)} />
          </div>
        ) : editingRule ? (
          <div style={{ background: '#141720', borderRadius: '12px', padding: '24px', marginBottom: '24px' }}>
            <h2 style={{ color: '#e8eaf0', fontSize: '18px', fontWeight: 600, marginBottom: '16px' }}>Edit Alert Rule</h2>
            <RuleForm initialData={editingRule} onSubmit={handleUpdate} onCancel={() => setEditingRule(null)} />
          </div>
        ) : null}

        <div style={{ background: '#141720', borderRadius: '12px', overflow: 'hidden' }}>
          <div style={{ padding: '16px 24px', borderBottom: '1px solid #252836' }}>
            <h2 style={{ color: '#e8eaf0', fontSize: '16px', fontWeight: 600 }}>Active Rules ({rules?.length || 0})</h2>
          </div>
          
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#1c1f2e', color: '#8b90a0', fontSize: '12px' }}>
                <th style={{ padding: '12px 16px', textAlign: 'left' }}>Rule Name</th>
                <th style={{ padding: '12px 16px', textAlign: 'left' }}>Scope</th>
                <th style={{ padding: '12px 16px', textAlign: 'left' }}>Momentum</th>
                <th style={{ padding: '12px 16px', textAlign: 'left' }}>Risk</th>
                <th style={{ padding: '12px 16px', textAlign: 'left' }}>Priority</th>
                <th style={{ padding: '12px 16px', textAlign: 'left' }}>Cooldown</th>
                <th style={{ padding: '12px 16px', textAlign: 'left' }}>Status</th>
                <th style={{ padding: '12px 16px', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rules && rules.length > 0 ? (
                rules.map((rule) => (
                  <tr key={rule.id} style={{ borderBottom: '1px solid #252836' }}>
                    <td style={{ padding: '12px 16px', color: '#e8eaf0' }}>{rule.name}</td>
                    <td style={{ padding: '12px 16px', color: '#8b90a0' }}>
                      {rule.is_global ? 'Global' : 'Token-specific'}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#8b90a0' }}>
                      {rule.momentum_threshold ? `≥${rule.momentum_threshold}` : 'Any'}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#8b90a0' }}>
                      {rule.risk_level_max ? `≤${rule.risk_level_max.toUpperCase()}` : 'Any'}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <PriorityBadge priority={rule.priority} />
                    </td>
                    <td style={{ padding: '12px 16px', color: '#8b90a0' }}>{rule.cooldown_minutes}m</td>
                    <td style={{ padding: '12px 16px' }}>
                      <RuleStatus enabled={rule.enabled} />
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                      <button
                        onClick={() => setEditingRule(rule)}
                        style={{
                          padding: '6px 12px',
                          marginRight: '8px',
                          background: '#1c1f2e',
                          border: '1px solid #252836',
                          borderRadius: '4px',
                          color: '#4f8ef7',
                          fontSize: '12px',
                          cursor: 'pointer',
                        }}
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(rule.id)}
                        style={{
                          padding: '6px 12px',
                          background: '#1c1f2e',
                          border: '1px solid #252836',
                          borderRadius: '4px',
                          color: '#ef4444',
                          fontSize: '12px',
                          cursor: 'pointer',
                        }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} style={{ padding: '24px', textAlign: 'center', color: '#8b90a0' }}>
                    No alert rules yet. Create your first rule above!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div style={{ marginTop: '24px', padding: '16px', background: '#1c1f2e', borderRadius: '6px' }}>
          <h3 style={{ color: '#e8eaf0', fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>How Alert Rules Work</h3>
          <ul style={{ color: '#8b90a0', fontSize: '13px', paddingLeft: '20px', margin: 0 }}>
            <li>Global rules apply to all tokens. Token-specific rules override global ones.</li>
            <li>Momentum threshold: minimum score required for alert (0-100).</li>
            <li>Max Risk Level: highest risk level that still triggers alert.</li>
            <li>Cooldown: minimum minutes between alerts for same token+rule.</li>
            <li>High priority rules appear first and can trigger alerts more frequently.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
