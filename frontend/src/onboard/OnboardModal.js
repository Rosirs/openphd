import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState } from 'react';
import { LLMConfigForm } from './LLMConfigForm';
export function OnboardModal({ providers, onSkip, onSave, onTest, }) {
    const [step, setStep] = useState('welcome');
    const [skipping, setSkipping] = useState(false);
    const handleSkip = async () => {
        setSkipping(true);
        try {
            await onSkip();
        }
        finally {
            setSkipping(false);
        }
    };
    return (_jsx("div", { className: "modal-backdrop", "data-testid": "onboard-modal", children: _jsx("div", { className: "modal", children: step === 'welcome' ? (_jsxs(_Fragment, { children: [_jsxs("h2", { children: ["Welcome to your ", _jsx("em", { children: "desk" }), "."] }), _jsxs("p", { children: ["PhD-Agent calls tools on your behalf \u2014 arxiv, email drafts, prose polish, PDF summaries. To make this feel like ", _jsx("em", { children: "your" }), " work, wire up an LLM."] }), _jsx("p", { className: "hint", children: "No API key handy? Skip to use the built-in mock LLM. You can change this any time from the gear in the header." }), _jsxs("div", { className: "actions", children: [_jsx("button", { className: "btn", onClick: handleSkip, disabled: skipping, "data-testid": "skip-btn", children: skipping ? 'Skipping…' : 'Skip (use mock)' }), _jsx("button", { className: "btn btn-primary", onClick: () => setStep('form'), "data-testid": "setup-btn", children: "Setup LLM" })] })] })) : (_jsxs(_Fragment, { children: [_jsxs("h2", { children: ["Configure your ", _jsx("em", { children: "model" })] }), _jsx("p", { className: "hint", children: "Pick a provider, drop in your key, then test the connection. The key stays on the server \u2014 only a masked preview is shown." }), _jsx(LLMConfigForm, { providers: providers, onSave: onSave, onCancel: () => setStep('welcome'), onTest: onTest })] })) }) }));
}
