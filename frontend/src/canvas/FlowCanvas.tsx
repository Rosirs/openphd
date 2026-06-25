import { useCallback, useMemo, useState } from 'react';
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  type Node,
  type Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import type { AgentContract } from '../api/types';
import { AgentNode } from './AgentNode';
import { usePipelineValidation } from './usePipelineValidation';

const nodeTypes = { agent: AgentNode };

interface Props {
  contracts: AgentContract[];
  onRun: (pipeline: string[]) => void;
}

export function FlowCanvas({ contracts, onRun }: Props) {
  const contractMap = useMemo(
    () => new Map(contracts.map(c => [c.agent_id, c])),
    [contracts],
  );
  const [pipeline, setPipeline] = useState<string[]>([]);

  const validation = usePipelineValidation(pipeline, contractMap);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const id = e.dataTransfer.getData('application/phd-agent-id');
    if (id) setPipeline(p => [...p, id]);
  }, []);

  const nodes: Node[] = useMemo(
    () =>
      pipeline.map((id, idx) => {
        const c = contractMap.get(id);
        const step = validation.steps[idx];
        return {
          id: `${idx}-${id}`,
          type: 'agent',
          position: { x: idx * 220, y: 100 },
          data: {
            ...c,
            hasMissingDeps: step ? !step.ok : false,
          },
        };
      }),
    [pipeline, contractMap, validation],
  );

  const edges: Edge[] = useMemo(
    () =>
      pipeline.slice(0, -1).map((_, idx) => ({
        id: `e${idx}-${idx + 1}`,
        source: `${idx}-${pipeline[idx]}`,
        target: `${idx + 1}-${pipeline[idx + 1]}`,
        style: {
          stroke:
            validation.steps[idx + 1]?.ok === false
              ? '#e53935'
              : validation.steps.every(s => s.ok)
                ? '#43a047'
                : '#888',
          strokeWidth: 2,
        },
      })),
    [pipeline, validation],
  );

  return (
    <div style={{ flex: 1, position: 'relative' }} onDrop={onDrop} onDragOver={e => e.preventDefault()}>
      <ReactFlowProvider>
        <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView>
          <Background />
        </ReactFlow>
      </ReactFlowProvider>
      <div style={{ position: 'absolute', top: 12, right: 12 }}>
        <button
          data-testid="run-btn"
          disabled={!validation.valid || pipeline.length === 0}
          onClick={() => onRun(pipeline)}
          style={{
            padding: '8px 16px',
            background: validation.valid ? '#43a047' : '#555',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            cursor: validation.valid ? 'pointer' : 'not-allowed',
          }}
        >
          {validation.valid ? '▶ Run Pipeline' : 'Fix errors to run'}
        </button>
      </div>
    </div>
  );
}
