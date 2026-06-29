import { useState } from 'react';
import type { ProviderInfo, SaveProfileBody, TestResponse } from '../api/types';
import { ProviderPicker } from './ProviderPicker';

const PRESETS: Record<string, { base_url: string; default_model: string }> = {
  openai: { base_url: 'https://api.openai.com/v1', default_model: 'gpt-4o-mini' },
  deepseek: { base_url: 'https://api.deepseek.com/v1', default_model: 'deepseek-chat' },
  moonshot: { base_url: 'https://api.moonshot.cn/v1', default_model: 'moonshot-v1-8k' },
  MiniMax: { base_url: 'https://api.MiniMax.chat/v1', default_model: 'MiniMax-M3' },
  custom: { base_url: '', default_model: '' },
  anthropic: { base_url: 'https://api.anthropic.com', default_model: 'claude-3-5-sonnet-20241022' },
};

export function LLMConfigForm({
  providers, initial, onSave, onCancel, onTest,
}: {
  providers: ProviderInfo[];
  initial?: Partial<SaveProfileBody>;
  onSave: (data: SaveProfileBody) => Promise<void> | void;
  onCancel?: () => void;
  onTest?: (data: SaveProfileBody) => Promise<TestResponse>;
}) {
  const [provider, setProvider] = useState(initial?.llm_provider || 'openai');
  const [baseUrl, setBaseUrl] = useState(initial?.base_url || PRESETS[provider].base_url);
  const [modelName, setModelName] = useState(initial?.model_name || PRESETS[provider].default_model);
  const [apiKey, setApiKey] = useState(initial?.api_key || '');
  const [showKey, setShowKey] = useState(false);
  const [testStatus, setTestStatus] = useState<TestResponse | null>(null);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);

  const onProviderChange = (k: string) => {
    setProvider(k);
    if (!initial?.base_url) setBaseUrl(PRESETS[k]?.base_url || '');
    if (!initial?.model_name) setModelName(PRESETS[k]?.default_model || '');
  };

  const data: SaveProfileBody = {
    llm_provider: provider, base_url: baseUrl,
    model_name: modelName, api_key: apiKey,
  };

  const handleTest = async () => {
    if (!onTest || !apiKey) return;
    setTesting(true);
    try {
      setTestStatus(await onTest(data));
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(data);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="llm-config-form" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <label>
        Provider
        <ProviderPicker providers={providers} value={provider} onChange={onProviderChange} />
      </label>
      <label>
        Base URL
        <input data-testid="base-url" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} />
      </label>
      <label>
        Model
        <input data-testid="model-name" value={modelName} onChange={(e) => setModelName(e.target.value)} />
      </label>
      <label>
        API Key
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            data-testid="api-key"
            type={showKey ? 'text' : 'password'}
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="sk-..."
            style={{ flex: 1 }}
          />
          <button
            type="button"
            className="btn"
            onClick={() => setShowKey(!showKey)}
            aria-label={showKey ? 'Hide key' : 'Show key'}
            title={showKey ? 'Hide key' : 'Show key'}
          >
            {showKey ? '🙈' : '👁'}
          </button>
        </div>
      </label>
      {testStatus && (
        <div className={testStatus.ok ? 'test-ok' : 'test-fail'}>
          {testStatus.ok ? '✓' : '✕'} {testStatus.message} ({testStatus.latency_ms}ms)
        </div>
      )}
      <div className="actions">
        {onCancel && (
          <button className="btn" onClick={onCancel}>Cancel</button>
        )}
        {onTest && (
          <button
            className="btn"
            data-testid="test-btn"
            onClick={handleTest}
            disabled={testing || !apiKey}
          >
            {testing ? 'Testing…' : 'Test connection'}
          </button>
        )}
        <button
          className="btn btn-primary"
          data-testid="save-btn"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? 'Saving…' : 'Save'}
        </button>
      </div>
    </div>
  );
}
