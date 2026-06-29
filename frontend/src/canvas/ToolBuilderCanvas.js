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
        setSavedMessage(`Saved "${toolId}" — switch to Chat to use it.`);
        api.listTools(userId).then(setTools).catch(console.error);
    };
    return (_jsxs("div", { className: "canvas-view", children: [_jsxs("div", { className: "canvas-intro", children: [_jsx("div", { className: "eyebrow", children: "The workshop" }), _jsxs("h2", { children: ["Compose your ", _jsx("em", { children: "own" }), " tool"] }), _jsx("p", { children: "Pick atomic tools from the shelf, chain them in order, then add a system prompt that names their purpose. The composite runs its own LLM loop and is callable from Chat like any other tool." })] }), _jsxs("div", { className: "canvas-body", children: [_jsxs("aside", { className: "shelf", children: [_jsxs("h3", { children: [_jsx("span", { children: "Shelf" }), _jsx("span", { className: "count", children: atomicTools.length })] }), atomicTools.length === 0 && (_jsx("p", { className: "hint", style: { fontStyle: 'italic' }, children: "No tools loaded." })), atomicTools.map(t => (_jsxs("button", { "data-testid": `add-${t.name}`, onClick: () => addTool(t.name), className: "tool-card", children: [_jsx("div", { className: "name", children: t.name }), _jsx("span", { className: "cat", children: t.category })] }, t.name)))] }), _jsxs("section", { className: "board", children: [_jsx("h3", { children: "Sub-pipeline" }), pipeline.length === 0 ? (_jsxs("div", { className: "pipeline-empty", children: [_jsx("div", { className: "glyph", children: "\u203B" }), _jsx("div", { children: "Click tools on the shelf to add them here." })] })) : (_jsx("div", { className: "pipeline", children: pipeline.map((id, idx) => {
                                    const t = toolMap.get(id);
                                    return (_jsxs("div", { className: "pipeline-step", children: [_jsx("span", { className: "num", children: String(idx + 1).padStart(2, '0') }), _jsx("span", { className: "name", children: id }), t && _jsx("span", { className: "cat", children: t.category }), _jsx("button", { className: "remove", onClick: () => removeTool(idx), "aria-label": `Remove ${id}`, title: "Remove", children: "\u00D7" })] }, `${id}-${idx}`));
                                }) })), _jsxs("div", { className: "canvas-actions", children: [_jsx("button", { "data-testid": "save-btn", className: "btn btn-primary", disabled: !validation.valid, onClick: () => setShowModal(true), children: "Save as my tool" }), savedMessage && (_jsxs("span", { className: "save-status", children: [_jsx("span", { "aria-hidden": "true", children: "\u25CF" }), savedMessage] }))] })] })] }), showModal && (_jsx(SaveToolModal, { subTools: pipeline, onClose: () => setShowModal(false), onSave: async (data) => {
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
