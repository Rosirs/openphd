import { useEffect, useState } from 'react';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { ToolCallIndicator } from './ToolCallIndicator';
import { api } from '../api/client';
import type { Message } from '../api/types';

export function ChatView({ userId }: { userId: string }) {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeTools, setActiveTools] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
        } else if (
          (ev.type === 'tool_call_completed' || ev.type === 'tool_call_skipped') && ev.name
        ) {
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
      setMessages((m) => [...m, {
        role: 'assistant', content: assistant, timestamp: new Date().toISOString(),
      }]);
    }
    setBusy(false);
  };

  return (
    <div className="chat-view">
      <MessageList messages={messages} />
      <ToolCallIndicator active={activeTools} />
      {error && <div className="chat-error">{error}</div>}
      <ChatInput onSend={send} disabled={busy || !conversationId} />
    </div>
  );
}
