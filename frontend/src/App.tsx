import { useEffect, useState } from 'react';
import { ChatView } from './chat/ChatView';
import { ToolBuilderCanvas } from './canvas/ToolBuilderCanvas';
import { OnboardModal } from './onboard/OnboardModal';
import { onboardApi } from './api/client';
import type { OnboardStatus, SaveProfileBody, TestResponse } from './api/types';
import './App.css';

type Tab = 'chat' | 'canvas';

export default function App() {
  const [tab, setTab] = useState<Tab>('chat');
  const [status, setStatus] = useState<OnboardStatus | null>(null);
  const [showOnboard, setShowOnboard] = useState(false);
  const userId = 'default-user';

  const refresh = async () => {
    const s = await onboardApi.getStatus();
    setStatus(s);
    if (!s.onboarded) setShowOnboard(true);
  };

  useEffect(() => { refresh().catch(console.error); }, []);

  const handleTest = async (data: SaveProfileBody): Promise<TestResponse> => {
    return await onboardApi.test(data);
  };

  const handleSave = async (data: SaveProfileBody) => {
    await onboardApi.save(data);
    await refresh();
  };

  const handleSkip = async () => {
    await onboardApi.skip();
    setShowOnboard(false);
    await refresh();
  };

  if (!status) {
    return (
      <div className="app" style={{ alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: 'var(--faded)', fontFamily: 'var(--font-display)', fontStyle: 'italic' }}>
          opening the desk…
        </div>
      </div>
    );
  }

  const providerLabel = status.profile
    ? `${status.profile.llm_provider} · ${status.profile.model_name}`
    : 'mock LLM';
  const isLive = !!status.profile;

  return (
    <div className="app">
      <aside className="rail">
        <div className="brand">
          <span className="brand-mark">PhD<em>·</em>Agent</span>
        </div>

        <nav className="nav" aria-label="Workspace sections">
          <div className="nav-label">Workspace</div>
          <button
            className={`nav-item ${tab === 'chat' ? 'active' : ''}`}
            onClick={() => setTab('chat')}
            data-testid="tab-chat"
          >
            <span className="glyph">§</span>
            <span>Chat</span>
          </button>
          <button
            className={`nav-item ${tab === 'canvas' ? 'active' : ''}`}
            onClick={() => setTab('canvas')}
            data-testid="tab-canvas"
          >
            <span className="glyph">‡</span>
            <span>Canvas</span>
          </button>
        </nav>

        <div className="rail-spacer" />

        <div className="provider-card">
          <div className="row">
            <span className="name">LLM</span>
            <span className={`status ${isLive ? 'live' : 'mock'}`}>
              {isLive ? 'live' : 'mock'}
            </span>
          </div>
          <span className="model">{providerLabel}</span>
        </div>
      </aside>

      <main className="work">
        {tab === 'chat' && <ChatView userId={userId} status={status} onProfileChange={refresh} />}
        {tab === 'canvas' && <ToolBuilderCanvas userId={userId} />}
      </main>

      {showOnboard && status && (
        <OnboardModal
          providers={status.providers}
          onSkip={handleSkip}
          onSave={async (data) => { await handleSave(data); setShowOnboard(false); }}
          onTest={handleTest}
        />
      )}
    </div>
  );
}
