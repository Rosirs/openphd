import { jsx as _jsx } from "react/jsx-runtime";
import { useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';
export function MessageList({ messages }) {
    const ref = useRef(null);
    useEffect(() => {
        const el = ref.current;
        if (el)
            el.scrollTop = el.scrollHeight;
    }, [messages]);
    return (_jsx("div", { className: "message-list", ref: ref, children: messages.map((m, i) => _jsx(MessageBubble, { msg: m }, i)) }));
}
