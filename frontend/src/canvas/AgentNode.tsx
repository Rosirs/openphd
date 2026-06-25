import { Handle, Position, type NodeProps, type Node } from '@xyflow/react';
import type { AgentContract } from '../api/types';

interface AgentNodeData extends Record<string, unknown>, AgentContract {
  hasMissingDeps: boolean;
}

export function AgentNode({ data }: NodeProps<Node<AgentNodeData>>) {
  const border = data.hasMissingDeps ? '#e53935' : '#43a047';
  return (
    <div
      style={{
        background: '#222',
        border: `2px solid ${border}`,
        borderRadius: 6,
        padding: 10,
        minWidth: 160,
        color: '#fff',
      }}
    >
      <Handle type="target" position={Position.Left} />
      <div style={{ fontWeight: 600 }}>{data.name}</div>
      <div style={{ fontSize: 11, color: '#aaa' }}>{data.agent_id}</div>
      {data.hasMissingDeps && (
        <div style={{ fontSize: 11, color: '#e53935', marginTop: 4 }}>
          ⚠ missing inputs
        </div>
      )}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
