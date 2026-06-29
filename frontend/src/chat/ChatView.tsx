import { useEffect, useState } from 'react';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { ToolCallIndicator } from './ToolCallIndicator';
import { SettingsModal } from '../onboard/SettingsModal';
import { api, onboardApi } from '../api/client';
import type { Message, OnboardStatus, SaveProfileBody, TestResponse } from '../api/types';

const STARTERS = [
  'Find me three recent papers on retrieval-augmented generation.',
  'Draft a polite email to a professor about joining their lab.',
  'Polish the introduction of my research statement.',
];

export function ChatView({
  userId, status: initialStatus, onProfileChange,
}: {
  userId: string;
  status: OnboardStatus;
  onProfileChange: () => Promise<void>;
}) {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeTools, setActiveTools] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [status, setStatus] = useState<OnboardStatus>(initialStatus);

  useEffect(() => { setStatus(initialStatus); }, [initialStatus]);

  useEffect(() => {
    api.createConversation(userId, 'New chat')
      .then((s) => setConversationId(s.conversation_id))
      .catch((e) => setError(String(e)));
  }, [userId]);

  const send = async (text: string) => {
    if (!conversationId || busy) return;
    setBusy(true);
    setError(null);
    const userMsg: Message = { role: 'user', content: text, timestamp: new Date().toISOString() };
    setMessages((m) => [...m, userMsg]);
    setActiveTools([]);

    let assistant = '';
    try {
      const { stream, close } = api.subscribeMessages(userId, conversationId, text);
      for await (const ev of stream) {
        if (ev.type === 'tool_call_started' && ev.name) {
          setActiveTools((a) => [...a, ev.name!]);
        } else if ((ev.type === 'tool_call_completed' || ev.type === 'tool_call_skipped') && ev.name) {
          setActiveTools((a) => a.filter((n) => n !== ev.name));
        } else if (ev.type === 'message_completed' && ev.content) {
          assistant = ev.content;
        } else if (ev.type === 'error') {
          setError(ev.message || 'unknown error');
        }
      }
      close();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
    if (assistant) {
      setMessages((m) => [...m, { role: 'assistant', content: assistant, timestamp: new Date().toISOString() }]);
    }
    setBusy(false);
  };

  const refreshStatus = async () => {
    const s = await onboardApi.getStatus();
    setStatus(s);
    await onProfileChange();
  };

  return (
    <div className="chat-view">
      <header className="manuscript-header">
        <span className="run-meta">PHDA / CHAT</span>
        <span className="run-title">a desk at night<strong>conversation</strong></span>
        <button
          data-testid="settings-btn"
          onClick={() => setShowSettings(true)}
          className="btn"
          style={{ padding: '6px 12px', fontSize: 12 }}
          aria-label="Settings"
          title="Settings"
        >
          ⚙
        </button>
      </header>

      <div className="chat-stage">
        {activeTools.length > 0 && <div className="brass-bar" aria-hidden="true" />}
        <MessageList messages={messages} starters={STARTERS} onPickStarter={send} busy={busy} />
        <ToolCallIndicator active={activeTools} />
        {error && <div className="chat-error">{error}</div>}
        <ChatInput onSend={send} disabled={busy || !conversationId} />
      </div>

      {showSettings && (
        <SettingsModal
          status={status}
          onClose={() => setShowSettings(false)}
          onSave={refreshStatus}
          onTest={async (data: SaveProfileBody) =>
            (await onboardApi.test(data)) as TestResponse}
        />
      )}
    </div>
  );
}
