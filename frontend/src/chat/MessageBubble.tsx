import type { Message } from '../api/types';

function pad(n: number, w = 2): string {
  return String(n).padStart(w, '0');
}

export function MessageBubble({ msg, index = 0 }: { msg: Message; index?: number }) {
  const anchor = `[${pad(index + 1)}]`;
  return (
    <div className={`bubble bubble-${msg.role}`}>
      <span className="anchor">{anchor}</span>
      <div className="role">
        {msg.role === 'user' ? 'You' : msg.role === 'assistant' ? 'Assistant' : msg.role}
      </div>
      {msg.content && <div className="content">{msg.content}</div>}
      {msg.tool_calls && msg.tool_calls.length > 0 && (
        <div className="tool-calls">
          {msg.tool_calls.map((tc) => (
            <code key={tc.id}>
              {tc.name}(<span className="arg">{JSON.stringify(tc.args)}</span>)
            </code>
          ))}
        </div>
      )}
    </div>
  );
}
