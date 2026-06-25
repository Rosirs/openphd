import type { AgentContract } from '../api/types';

interface Props {
  contract: AgentContract;
  onDragStart: (agentId: string) => void;
}

export function AgentCard({ contract, onDragStart }: Props) {
  return (
    <div
      draggable
      onDragStart={e => {
        e.dataTransfer.setData('application/phd-agent-id', contract.agent_id);
        onDragStart(contract.agent_id);
      }}
      style={{
        border: '1px solid #444',
        borderRadius: 8,
        padding: 12,
        marginBottom: 8,
        cursor: 'grab',
        background: '#1a1a1a',
      }}
      title={`Requires: ${contract.required_fields.join(', ') || '(none)'}`}
    >
      <div style={{ fontWeight: 600 }}>{contract.name}</div>
      <div style={{ fontSize: 12, color: '#aaa' }}>{contract.category}</div>
      <div style={{ fontSize: 11, color: '#888', marginTop: 4 }}>
        {contract.required_fields.length > 0
          ? `Needs: ${contract.required_fields.join(', ')}`
          : 'No prerequisites'}
      </div>
    </div>
  );
}
