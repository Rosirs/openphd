import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useMemo, useState } from 'react';
import { api } from '../api/client';
import { SaveToolModal } from './SaveToolModal';
export function ToolBuilderCanvas({ userId }) {
    const [tools, setTools] = useState([]);
    const [pipeline, setPipeline] = useState([]);
    const [showModal, setShowModal] = useState(false);
    const [savedMessage, setSavedMessage] = useState(null);
    useEffect(() => {
        api.listTools(userId).then(setTools).catch(console.error);
    }, [userId]);
    const toolMap = useMemo(() => new Map(tools.map(t => [t.name, t])), [tools]);
    const atomicTools = tools.filter(t => t.category !== 'composite');
    const validation = useMemo(() => {
        // Phase 2: simple validation - composite tool just needs ≥ 1 atomic sub-tool
        if (pipeline.length === 0)
            return { valid: false, reason: 'empty' };
        for (const id of pipeline) {
            if (!toolMap.has(id))
                return { valid: false, reason: `unknown tool: ${id}` };
        }
        return { valid: true, reason: '' };
    }, [pipeline, toolMap]);
    const addTool = (id) => setPipeline(p => [...p, id]);
    const removeTool = (idx) => setPipeline(p => p.filter((_, i) => i !== idx));
    const handleSaved = (toolId) => {
        setShowModal(false);
        setPipeline([]);
        setSavedMessage(`Saved as "${toolId}". Switch to Chat to use it.`);
        // Refresh tool list
        api.listTools(userId).then(setTools).catch(console.error);
    };
    return (_jsxs("div", { className: "tool-builder-canvas", children: [_jsx("h2", { children: "Custom Tool Builder" }), _jsx("p", { className: "info", children: "Drag (click) tools from the shelf to compose a custom tool. When you save, it becomes available in Chat for the LLM to call. The composite tool runs its own LLM loop with the listed sub-tools." }), savedMessage && _jsx("div", { className: "chat-error", style: { color: '#8f8' }, children: savedMessage }), _jsxs("div", { style: { display: 'flex', gap: 16, flex: 1, overflow: 'hidden' }, children: [_jsxs("div", { style: { flex: '0 0 240px', overflowY: 'auto' }, children: [_jsxs("h3", { style: { fontSize: '0.9em' }, children: ["Tools (", atomicTools.length, ")"] }), atomicTools.map(t => (_jsxs("button", { "data-testid": `add-${t.name}`, onClick: () => addTool(t.name), style: {
                                    display: 'block', width: '100%', textAlign: 'left',
                                    padding: '6px 8px', marginBottom: 4,
                                    background: '#1a1a1a', color: '#fff', border: '1px solid #333',
                                    borderRadius: 3, cursor: 'pointer', fontSize: '0.85em',
                                }, children: [_jsx("div", { children: t.name }), _jsx("div", { style: { color: '#888', fontSize: '0.8em' }, children: t.category })] }, t.name)))] }), _jsxs("div", { style: { flex: 1, display: 'flex', flexDirection: 'column' }, children: [_jsx("h3", { style: { fontSize: '0.9em' }, children: "Sub-pipeline" }), _jsxs("div", { style: {
                                    flex: 1, background: '#0a0a0a', border: '1px solid #222',
                                    borderRadius: 4, padding: 8, overflowY: 'auto',
                                }, children: [pipeline.length === 0 && (_jsx("div", { style: { color: '#666' }, children: "Click tools on the left to add." })), pipeline.map((id, idx) => (_jsxs("div", { style: {
                                            display: 'flex', alignItems: 'center', gap: 8,
                                            padding: 8, background: '#1a1a1a', borderRadius: 4, marginBottom: 4,
                                        }, children: [_jsxs("span", { style: { color: '#888' }, children: [idx + 1, "."] }), _jsx("span", { style: { flex: 1 }, children: id }), _jsx("button", { onClick: () => removeTool(idx), style: {
                                                    background: 'transparent', color: '#f88',
                                                    border: '1px solid #633', borderRadius: 3, padding: '2px 8px',
                                                    cursor: 'pointer',
                                                }, children: "\u00D7" })] }, idx)))] }), _jsx("div", { style: { marginTop: 12, display: 'flex', gap: 8 }, children: _jsx("button", { "data-testid": "save-btn", disabled: !validation.valid, onClick: () => setShowModal(true), style: {
                                        padding: '8px 16px',
                                        background: validation.valid ? '#43a047' : '#555',
                                        color: '#fff', border: 'none', borderRadius: 4,
                                        cursor: validation.valid ? 'pointer' : 'not-allowed',
                                    }, children: "Save as my tool" }) })] })] }), showModal && (_jsx(SaveToolModal, { subTools: pipeline, onClose: () => setShowModal(false), onSave: async (data) => {
                    await api.saveComposite(userId, {
                        tool_id: data.tool_id,
                        name: data.name,
                        description: data.system_prompt,
                        system_prompt: data.system_prompt,
                        sub_tools: pipeline,
                    });
                    handleSaved(data.tool_id);
                } }))] }));
}
