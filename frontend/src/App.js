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
        return _jsx("div", { style: { padding: 24 }, children: "Loading\u2026" });
    }
    return (_jsxs("div", { className: "app", children: [_jsxs("header", { className: "tabs", children: [_jsx("button", { className: tab === 'chat' ? 'active' : '', onClick: () => setTab('chat'), children: "Chat" }), _jsx("button", { className: tab === 'canvas' ? 'active' : '', onClick: () => setTab('canvas'), children: "Canvas" })] }), _jsxs("main", { children: [tab === 'chat' && _jsx(ChatView, { userId: userId, status: status, onProfileChange: refresh }), tab === 'canvas' && _jsx(ToolBuilderCanvas, { userId: userId })] }), showOnboard && status && (_jsx(OnboardModal, { providers: status.providers, onSkip: handleSkip, onSave: async (data) => { await handleSave(data); setShowOnboard(false); }, onTest: handleTest }))] }));
}
