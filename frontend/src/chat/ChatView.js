import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { ToolCallIndicator } from './ToolCallIndicator';
import { SettingsModal } from '../onboard/SettingsModal';
import { api, onboardApi } from '../api/client';
export function ChatView({ userId, status: initialStatus, onProfileChange, }) {
    const [conversationId, setConversationId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [activeTools, setActiveTools] = useState([]);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState(null);
    const [showSettings, setShowSettings] = useState(false);
    const [status, setStatus] = useState(initialStatus);
    useEffect(() => { setStatus(initialStatus); }, [initialStatus]);
    useEffect(() => {
        api.createConversation(userId, 'New chat')
            .then((s) => setConversationId(s.conversation_id))
            .catch((e) => setError(String(e)));
    }, [userId]);
    const send = async (text) => {
        if (!conversationId || busy)
            return;
        setBusy(true);
        setError(null);
        const userMsg = { role: 'user', content: text, timestamp: new Date().toISOString() };
        setMessages((m) => [...m, userMsg]);
        setActiveTools([]);
        let assistant = '';
        try {
            const { stream, close } = api.subscribeMessages(userId, conversationId, text);
            for await (const ev of stream) {
                if (ev.type === 'tool_call_started' && ev.name) {
                    setActiveTools((a) => [...a, ev.name]);
                }
                else if ((ev.type === 'tool_call_completed' || ev.type === 'tool_call_skipped') && ev.name) {
                    setActiveTools((a) => a.filter((n) => n !== ev.name));
                }
                else if (ev.type === 'message_completed' && ev.content) {
                    assistant = ev.content;
                }
                else if (ev.type === 'error') {
                    setError(ev.message || 'unknown error');
                }
            }
            close();
        }
        catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        }
        if (assistant) {
            setMessages((m) => [...m, { role: 'assistant', content: assistant, timestamp: new Date().toISOString() }]);
        }
        setBusy(false);
    };
    const refreshStatus = async () => {
        const s = await onboardApi.getStatus();
        setStatus(s);
        await onProfileChange();
    };
    const providerLabel = status.profile
        ? `${status.profile.llm_provider} · ${status.profile.model_name}`
        : 'mock LLM';
    return (_jsxs("div", { className: "chat-view", children: [_jsxs("header", { className: "chat-header", children: [_jsx("span", { className: "logo", children: "PhD-Agent" }), _jsx("span", { className: "provider-tag", children: providerLabel }), _jsx("button", { "data-testid": "settings-btn", onClick: () => setShowSettings(true), className: "icon-btn", children: "\u2699" })] }), _jsx(MessageList, { messages: messages }), _jsx(ToolCallIndicator, { active: activeTools }), error && _jsx("div", { className: "chat-error", children: error }), _jsx(ChatInput, { onSend: send, disabled: busy || !conversationId }), showSettings && (_jsx(SettingsModal, { status: status, onClose: () => setShowSettings(false), onSave: refreshStatus, onTest: async (data) => (await onboardApi.test(data)) }))] }));
}
