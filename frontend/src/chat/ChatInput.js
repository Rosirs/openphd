import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
export function ChatInput({ onSend, disabled, }) {
    const [text, setText] = useState('');
    const submit = (e) => {
        e.preventDefault();
        if (!text.trim() || disabled)
            return;
        onSend(text);
        setText('');
    };
    return (_jsxs("form", { className: "chat-input", onSubmit: submit, children: [_jsx("input", { value: text, onChange: (e) => setText(e.target.value), placeholder: "Ask anything\u2026", disabled: disabled, autoFocus: true }), _jsx("button", { type: "submit", disabled: disabled || !text.trim(), children: "Send" })] }));
}
