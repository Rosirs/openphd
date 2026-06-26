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
    return (_jsx("div", { className: "modal-backdrop", "data-testid": "onboard-modal", children: _jsx("div", { className: "modal", children: step === 'welcome' ? (_jsxs(_Fragment, { children: [_jsx("h2", { children: "Welcome to PhD-Agent" }), _jsx("p", { children: "Configure your LLM to start chatting with the AI assistant." }), _jsx("p", { className: "hint", children: "No API key? Skip to use the local mock LLM (you can configure later)." }), _jsxs("div", { className: "actions", children: [_jsx("button", { "data-testid": "setup-btn", onClick: () => setStep('form'), children: "Setup LLM" }), _jsx("button", { "data-testid": "skip-btn", onClick: handleSkip, disabled: skipping, children: skipping ? 'Skipping...' : 'Skip (use mock)' })] })] })) : (_jsxs(_Fragment, { children: [_jsx("h2", { children: "LLM Setup" }), _jsx(LLMConfigForm, { providers: providers, onSave: onSave, onCancel: () => setStep('welcome'), onTest: onTest })] })) }) }));
}
