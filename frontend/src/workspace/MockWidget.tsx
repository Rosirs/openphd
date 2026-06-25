interface Props {
  data: Record<string, unknown>;
  agentId: string;
}

export function MockWidget({ data, agentId }: Props) {
  return (
    <div
      data-testid={`widget-${agentId}`}
      style={{
        background: '#1a1a1a',
        border: '1px solid #444',
        borderRadius: 6,
        padding: 12,
        marginBottom: 12,
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 6 }}>{agentId} widget</div>
      <pre style={{ fontSize: 11, color: '#aaa', margin: 0, overflow: 'auto' }}>
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}
