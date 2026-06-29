import { useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';
import type { Message } from '../api/types';

export function MessageList({
  messages, starters, onPickStarter, busy,
}: {
  messages: Message[];
  starters?: string[];
  onPickStarter?: (text: string) => void;
  busy?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="message-list" ref={ref}>
        <div className="empty-state">
          <h1>What are you <em>working on</em>?</h1>
          <p>Pick a thread below or type your own — the assistant can search arxiv, draft emails, polish prose, and read PDFs.</p>
          {starters && (
            <div className="examples">
              {starters.map((s) => (
                <button
                  key={s}
                  className="example"
                  disabled={busy}
                  onClick={() => onPickStarter?.(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="message-list" ref={ref}>
      {messages.map((m, i) => (
        <MessageBubble key={i} msg={m} index={i + 1} />
      ))}
    </div>
  );
}
