import { useState, useEffect, useRef, type FormEvent, type KeyboardEvent } from 'react';

export function ChatInput({
  onSend, disabled,
}: { onSend: (text: string) => void; disabled: boolean }) {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Bring the cursor back whenever the composer becomes interactive again —
  // on mount, after each assistant reply finishes, and after clicks on the
  // empty-state starters — so the user never has to click the box to keep typing.
  useEffect(() => {
    if (!disabled) {
      textareaRef.current?.focus();
    }
  }, [disabled]);

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText('');
  };
  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };
  return (
    <form className="chat-input" onSubmit={submit}>
      <div className="editor">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask anything…"
          disabled={disabled}
          rows={1}
        />
        <div className="editor-meta">
          <span className="hint">
            <kbd>Enter</kbd> to send · <kbd>Shift</kbd>+<kbd>Enter</kbd> for newline
          </span>
          <span className="hint">{text.length.toLocaleString()} chars</span>
        </div>
      </div>
      <button type="submit" className="send" disabled={disabled || !text.trim()}>
        Send <span aria-hidden="true">→</span>
      </button>
    </form>
  );
}
