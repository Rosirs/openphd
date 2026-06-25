import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { api } from '../api/client';
export function SaveToolModal({ subTools, onSave, onClose, }) {
    const [toolId, setToolId] = useState('');
    const [name, setName] = useState('');
    const [systemPrompt, setSystemPrompt] = useState('');
    const [preview, setPreview] = useState('');
    useEffect(() => {
        if (name || systemPrompt) {
            api.previewPrompt(name || 'Tool', systemPrompt, subTools)
                .then(setPreview)
                .catch(() => setPreview(''));
        }
    }, [name, systemPrompt, subTools]);
    return (_jsx("div", { className: "modal-backdrop", onClick: onClose, children: _jsxs("div", { className: "modal", onClick: (e) => e.stopPropagation(), children: [_jsx("h2", { children: "Save as my tool" }), _jsxs("label", { children: ["Tool ID (unique, lowercase)", _jsx("input", { "data-testid": "tool-id", value: toolId, onChange: (e) => setToolId(e.target.value.replace(/[^a-z0-9_]/g, '_')), placeholder: "my_research_finder" })] }), _jsxs("label", { children: ["Name", _jsx("input", { "data-testid": "tool-name", value: name, onChange: (e) => setName(e.target.value), placeholder: "My Research Finder" })] }), _jsxs("label", { children: ["System Prompt (your intent \u2014 what should this tool do?)", _jsx("textarea", { "data-testid": "tool-prompt", value: systemPrompt, onChange: (e) => setSystemPrompt(e.target.value), placeholder: "Search arxiv for recent papers and polish the summary." })] }), _jsxs("p", { className: "sub-tools", children: ["Sub-tools: ", subTools.join(', ')] }), preview && (_jsxs("details", { children: [_jsx("summary", { style: { cursor: 'pointer', color: '#8cf' }, children: "Preview augmented prompt" }), _jsx("pre", { style: {
                                background: '#000', padding: 8, fontSize: '0.8em',
                                whiteSpace: 'pre-wrap', maxHeight: 200, overflowY: 'auto',
                            }, children: preview })] })), _jsxs("div", { className: "actions", children: [_jsx("button", { onClick: onClose, children: "Cancel" }), _jsx("button", { "data-testid": "modal-save", disabled: !toolId || !name, onClick: () => onSave({ tool_id: toolId, name, system_prompt: systemPrompt }), children: "Save" })] })] }) }));
}
