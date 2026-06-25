import { Handle, Position, type NodeProps, type Node } from '@xyflow/react';
import type { AgentContract } from '../api/types';

interface AgentNodeData extends Record<string, unknown>, AgentContract {
  hasMissingDeps: boolean;
  pipelineValid: boolean;
  missingFields: string[];
  onRemove: () => void;
}

export function AgentNode({ data }: NodeProps<Node<AgentNodeData>>) {
  const isError = data.hasMissingDeps || !data.pipelineValid;
  const border = isError ? '#e53935' : '#43a047';
  return (
    <div
      style={{
        background: '#222',
        border: `2px solid ${border}`,
        borderRadius: 6,
        padding: 10,
        minWidth: 160,
        color: '#fff',
        position: 'relative',
      }}
    >
      <Handle type="target" position={Position.Left} />
      <button
        onClick={data.onRemove}
        title="Remove from pipeline"
        style={{
          position: 'absolute', top: 4, right: 4,
          background: 'transparent', border: 'none', color: '#888',
          fontSize: 16, lineHeight: 1, cursor: 'pointer', padding: 2,
        }}
      >×</button>
      <div style={{ fontWeight: 600, paddingRight: 16 }}>{data.name}</div>
      <div style={{ fontSize: 11, color: '#aaa' }}>{data.agent_id}</div>
      {isError && (
        <>
          <div style={{ fontSize: 11, color: '#e53935', marginTop: 4 }}>
            ⚠ missing inputs
          </div>
          {data.missingFields.map(f => (
            <div key={f} style={{ fontSize: 10, color: '#e53935', marginTop: 2 }}>
              ✗ {f}
            </div>
          ))}
        </>
      )}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}