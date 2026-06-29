import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';
export function MessageList({ messages, starters, onPickStarter, busy, }) {
    const ref = useRef(null);
    useEffect(() => {
        const el = ref.current;
        if (el)
            el.scrollTop = el.scrollHeight;
    }, [messages]);
    if (messages.length === 0) {
        return (_jsx("div", { className: "message-list", ref: ref, children: _jsxs("div", { className: "empty-state", children: [_jsxs("h1", { children: ["What are you ", _jsx("em", { children: "working on" }), "?"] }), _jsx("p", { children: "Pick a thread below or type your own \u2014 the assistant can search arxiv, draft emails, polish prose, and read PDFs." }), starters && (_jsx("div", { className: "examples", children: starters.map((s) => (_jsx("button", { className: "example", disabled: busy, onClick: () => onPickStarter?.(s), children: s }, s))) }))] }) }));
    }
    return (_jsx("div", { className: "message-list", ref: ref, children: messages.map((m, i) => (_jsx(MessageBubble, { msg: m, index: i + 1 }, i))) }));
}
