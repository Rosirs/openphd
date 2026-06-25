import { useState, type FormEvent } from 'react';

export function ChatInput({
  onSend, disabled,
}: { onSend: (text: string) => void; disabled: boolean }) {
  const [text, setText] = useState('');
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!text.trim() || disabled) return;
    onSend(text);
    setText('');
  };
  return (
    <form className="chat-input" onSubmit={submit}>
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Ask anything…"
        disabled={disabled}
        autoFocus
      />
      <button type="submit" disabled={disabled || !text.trim()}>Send</button>
    </form>
  );
}
