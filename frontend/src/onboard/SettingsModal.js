import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { LLMConfigForm } from './LLMConfigForm';
export function SettingsModal({ status, onClose, onSave, onTest, }) {
    return (_jsx("div", { className: "modal-backdrop", "data-testid": "settings-modal", onClick: onClose, children: _jsxs("div", { className: "modal", onClick: (e) => e.stopPropagation(), children: [_jsxs("h2", { children: ["LLM ", _jsx("em", { children: "settings" })] }), status.profile ? (_jsxs("p", { className: "hint", children: ["Current: ", _jsx("strong", { children: status.profile.llm_provider }), " \u00B7 ", status.profile.model_name, _jsx("br", {}), "Key: ", _jsx("code", { style: { fontFamily: 'var(--font-mono)', color: 'var(--verdigris)' }, children: status.profile.api_key_masked })] })) : (_jsx("p", { className: "hint", children: "No LLM configured yet \u2014 using the built-in mock." })), _jsx(LLMConfigForm, { providers: status.providers, initial: status.profile ? {
                        llm_provider: status.profile.llm_provider,
                        base_url: status.profile.base_url,
                        model_name: status.profile.model_name,
                    } : undefined, onSave: async (data) => { await onSave(data); onClose(); }, onCancel: onClose, onTest: onTest })] }) }));
}
