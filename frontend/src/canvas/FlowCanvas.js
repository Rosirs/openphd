import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useCallback, useMemo, useState } from 'react';
import { ReactFlow, ReactFlowProvider, Background, } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { AgentNode } from './AgentNode';
import { usePipelineValidation } from './usePipelineValidation';
const nodeTypes = { agent: AgentNode };
export function FlowCanvas({ contracts, onRun }) {
    const contractMap = useMemo(() => new Map(contracts.map(c => [c.agent_id, c])), [contracts]);
    const [pipeline, setPipeline] = useState([]);
    const validation = usePipelineValidation(pipeline, contractMap);
    const onDrop = useCallback((e) => {
        e.preventDefault();
        const id = e.dataTransfer.getData('application/phd-agent-id');
        if (id)
            setPipeline(p => [...p, id]);
    }, []);
    const handleRemove = useCallback((idx) => {
        setPipeline(p => p.filter((_, i) => i !== idx));
    }, []);
    const nodes = useMemo(() => pipeline.map((id, idx) => {
        const c = contractMap.get(id);
        const step = validation.steps[idx];
        return {
            id: `${idx}-${id}`,
            type: 'agent',
            position: { x: idx * 220, y: 100 },
            data: {
                ...c,
                hasMissingDeps: step ? !step.ok : false,
                pipelineValid: validation.valid,
                missingFields: step ? [...step.missing] : [],
                onRemove: () => handleRemove(idx),
            },
        };
    }), [pipeline, contractMap, validation, handleRemove]);
    const edges = useMemo(() => pipeline.slice(0, -1).map((_, idx) => ({
        id: `e${idx}-${idx + 1}`,
        source: `${idx}-${pipeline[idx]}`,
        target: `${idx + 1}-${pipeline[idx + 1]}`,
        style: {
            stroke: validation.valid ? '#43a047' : '#e53935',
            strokeWidth: 2,
        },
    })), [pipeline, validation]);
    return (_jsxs("div", { style: { flex: 1, position: 'relative' }, onDrop: onDrop, onDragOver: e => e.preventDefault(), children: [_jsx(ReactFlowProvider, { children: _jsx(ReactFlow, { nodes: nodes, edges: edges, nodeTypes: nodeTypes, fitView: true, children: _jsx(Background, {}) }) }), _jsx("div", { style: { position: 'absolute', top: 12, right: 12 }, children: _jsx("button", { "data-testid": "run-btn", disabled: !validation.valid || pipeline.length === 0, onClick: () => onRun(pipeline), style: {
                        padding: '8px 16px',
                        background: validation.valid ? '#43a047' : '#555',
                        color: '#fff',
                        border: 'none',
                        borderRadius: 4,
                        cursor: validation.valid ? 'pointer' : 'not-allowed',
                    }, children: validation.valid ? '▶ Run Pipeline' : 'Fix errors to run' }) })] }));
}
