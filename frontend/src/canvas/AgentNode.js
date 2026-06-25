import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { Handle, Position } from '@xyflow/react';
export function AgentNode({ data }) {
    const isError = data.hasMissingDeps || !data.pipelineValid;
    const border = isError ? '#e53935' : '#43a047';
    return (_jsxs("div", { style: {
            background: '#222',
            border: `2px solid ${border}`,
            borderRadius: 6,
            padding: 10,
            minWidth: 160,
            color: '#fff',
            position: 'relative',
        }, children: [_jsx(Handle, { type: "target", position: Position.Left }), _jsx("button", { onClick: data.onRemove, title: "Remove from pipeline", style: {
                    position: 'absolute', top: 4, right: 4,
                    background: 'transparent', border: 'none', color: '#888',
                    fontSize: 16, lineHeight: 1, cursor: 'pointer', padding: 2,
                }, children: "\u00D7" }), _jsx("div", { style: { fontWeight: 600, paddingRight: 16 }, children: data.name }), _jsx("div", { style: { fontSize: 11, color: '#aaa' }, children: data.agent_id }), isError && (_jsxs(_Fragment, { children: [_jsx("div", { style: { fontSize: 11, color: '#e53935', marginTop: 4 }, children: "\u26A0 missing inputs" }), data.missingFields.map(f => (_jsxs("div", { style: { fontSize: 10, color: '#e53935', marginTop: 2 }, children: ["\u2717 ", f] }, f)))] })), _jsx(Handle, { type: "source", position: Position.Right })] }));
}
