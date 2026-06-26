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
    return <div style={{ padding: 24 }}>Loading…</div>;
  }

  return (
    <div className="app">
      <header className="tabs">
        <button className={tab === 'chat' ? 'active' : ''} onClick={() => setTab('chat')}>Chat</button>
        <button className={tab === 'canvas' ? 'active' : ''} onClick={() => setTab('canvas')}>Canvas</button>
      </header>
      <main>
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