import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { ChatView } from './chat/ChatView';
import { ToolBuilderCanvas } from './canvas/ToolBuilderCanvas';
import { OnboardModal } from './onboard/OnboardModal';
import { onboardApi } from './api/client';
import './App.css';
export default function App() {
    const [tab, setTab] = useState('chat');
    const [status, setStatus] = useState(null);
    const [showOnboard, setShowOnboard] = useState(false);
    const userId = 'default-user';
    const refresh = async () => {
        const s = await onboardApi.getStatus();
        setStatus(s);
        if (!s.onboarded)
            setShowOnboard(true);
    };
    useEffect(() => { refresh().catch(console.error); }, []);
    const handleTest = async (data) => {
        return await onboardApi.test(data);
    };
    const handleSave = async (data) => {
        await onboardApi.save(data);
        await refresh();
    };
    const handleSkip = async () => {
        await onboardApi.skip();
        setShowOnboard(false);
        await refresh();
    };
    if (!status) {
        return (_jsx("div", { className: "app", style: { alignItems: 'center', justifyContent: 'center' }, children: _jsx("div", { style: { color: 'var(--faded)', fontFamily: 'var(--font-display)', fontStyle: 'italic' }, children: "opening the desk\u2026" }) }));
    }
    const providerLabel = status.profile
        ? `${status.profile.llm_provider} · ${status.profile.model_name}`
        : 'mock LLM';
    const isLive = !!status.profile;
    return (_jsxs("div", { className: "app", children: [_jsxs("aside", { className: "rail", children: [_jsx("div", { className: "brand", children: _jsxs("span", { className: "brand-mark", children: ["PhD", _jsx("em", { children: "\u00B7" }), "Agent"] }) }), _jsxs("nav", { className: "nav", "aria-label": "Workspace sections", children: [_jsx("div", { className: "nav-label", children: "Workspace" }), _jsxs("button", { className: `nav-item ${tab === 'chat' ? 'active' : ''}`, onClick: () => setTab('chat'), "data-testid": "tab-chat", children: [_jsx("span", { className: "glyph", children: "\u00A7" }), _jsx("span", { children: "Chat" })] }), _jsxs("button", { className: `nav-item ${tab === 'canvas' ? 'active' : ''}`, onClick: () => setTab('canvas'), "data-testid": "tab-canvas", children: [_jsx("span", { className: "glyph", children: "\u2021" }), _jsx("span", { children: "Canvas" })] })] }), _jsx("div", { className: "rail-spacer" }), _jsxs("div", { className: "provider-card", children: [_jsxs("div", { className: "row", children: [_jsx("span", { className: "name", children: "LLM" }), _jsx("span", { className: `status ${isLive ? 'live' : 'mock'}`, children: isLive ? 'live' : 'mock' })] }), _jsx("span", { className: "model", children: providerLabel })] })] }), _jsxs("main", { className: "work", children: [tab === 'chat' && _jsx(ChatView, { userId: userId, status: status, onProfileChange: refresh }), tab === 'canvas' && _jsx(ToolBuilderCanvas, { userId: userId })] }), showOnboard && status && (_jsx(OnboardModal, { providers: status.providers, onSkip: handleSkip, onSave: async (data) => { await handleSave(data); setShowOnboard(false); }, onTest: handleTest }))] }));
}
