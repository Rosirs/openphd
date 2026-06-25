import type { Message } from '../api/types';

export function MessageBubble({ msg }: { msg: Message }) {
  return (
    <div className={`bubble bubble-${msg.role}`}>
      <div className="role">{msg.role}</div>
      {msg.content && <div className="content">{msg.content}</div>}
      {msg.tool_calls && msg.tool_calls.length > 0 && (
        <div className="tool-calls">
          {msg.tool_calls.map((tc) => (
            <code key={tc.id}>{tc.name}({JSON.stringify(tc.args)})</code>
          ))}
        </div>
      )}
    </div>
  );
}
