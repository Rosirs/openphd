import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { ToolCallIndicator } from './ToolCallIndicator';
import { api } from '../api/client';
export function ChatView({ userId }) {
    const [conversationId, setConversationId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [activeTools, setActiveTools] = useState([]);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState(null);
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
            setMessages((m) => [...m, {
                    role: 'assistant', content: assistant, timestamp: new Date().toISOString(),
                }]);
        }
        setBusy(false);
    };
    return (_jsxs("div", { className: "chat-view", children: [_jsx(MessageList, { messages: messages }), _jsx(ToolCallIndicator, { active: activeTools }), error && _jsx("div", { className: "chat-error", children: error }), _jsx(ChatInput, { onSend: send, disabled: busy || !conversationId })] }));
}
