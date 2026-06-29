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
    return (_jsx("div", { className: "modal-backdrop", onClick: onClose, children: _jsxs("div", { className: "modal wide", onClick: (e) => e.stopPropagation(), children: [_jsxs("h2", { children: ["Save as ", _jsx("em", { children: "my tool" })] }), _jsx("p", { className: "hint", children: "Name it, give it an ID, and describe what it does. The system prompt and the sub-pipeline are sent to the LLM together." }), _jsxs("label", { children: ["Tool ID", _jsx("input", { "data-testid": "tool-id", value: toolId, onChange: (e) => setToolId(e.target.value.replace(/[^a-z0-9_]/g, '_')), placeholder: "my_research_finder" })] }), _jsxs("label", { children: ["Name", _jsx("input", { "data-testid": "tool-name", value: name, onChange: (e) => setName(e.target.value), placeholder: "My Research Finder" })] }), _jsxs("label", { children: ["System prompt \u2014 what should this tool do?", _jsx("textarea", { "data-testid": "tool-prompt", value: systemPrompt, onChange: (e) => setSystemPrompt(e.target.value), placeholder: "Search arxiv for recent papers and polish the summary." })] }), _jsxs("div", { className: "sub-tools", children: ["Sub-tools: ", subTools.join(' › ')] }), preview && (_jsxs("details", { children: [_jsx("summary", { children: "Preview augmented prompt" }), _jsx("pre", { className: "preview-box", children: preview })] })), _jsxs("div", { className: "actions", children: [_jsx("button", { className: "btn", onClick: onClose, children: "Cancel" }), _jsx("button", { className: "btn btn-primary", "data-testid": "modal-save", disabled: !toolId || !name, onClick: () => onSave({ tool_id: toolId, name, system_prompt: systemPrompt }), children: "Save" })] })] }) }));
}
