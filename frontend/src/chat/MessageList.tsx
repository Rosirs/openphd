import { useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';
import type { Message } from '../api/types';

export function MessageList({ messages }: { messages: Message[] }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);
  return (
    <div className="message-list" ref={ref}>
      {messages.map((m, i) => <MessageBubble key={i} msg={m} />)}
    </div>
  );
}
