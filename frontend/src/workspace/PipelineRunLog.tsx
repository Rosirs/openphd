import type { SseEvent } from '../api/types';

interface Props {
  events: SseEvent[];
}

export function PipelineRunLog({ events }: Props) {
  return (
    <div data-testid="run-log" style={{ marginBottom: 16 }}>
      <h4 style={{ margin: '0 0 8px' }}>Run Log</h4>
      <div
        style={{
          background: '#000',
          color: '#0f0',
          fontFamily: 'monospace',
          fontSize: 12,
          padding: 8,
          borderRadius: 4,
          maxHeight: 200,
          overflowY: 'auto',
        }}
      >
        {events.length === 0
          ? <div style={{ color: '#666' }}>(no events yet)</div>
          : events.map((e, i) => (
              <div key={i}>
                [{e.step}] {e.agent_id || '(end)'} — {e.status} ({e.duration_ms}ms)
                {e.error && <span style={{ color: '#e53935' }}> ⚠ {e.error}</span>}
              </div>
            ))}
      </div>
    </div>
  );
}
