import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect, useRef } from 'react';
export function ChatInput({ onSend, disabled, }) {
    const [text, setText] = useState('');
    const textareaRef = useRef(null);
    // Bring the cursor back whenever the composer becomes interactive again —
    // on mount, after each assistant reply finishes, and after clicks on the
    // empty-state starters — so the user never has to click the box to keep typing.
    useEffect(() => {
        if (!disabled) {
            textareaRef.current?.focus();
        }
    }, [disabled]);
    const submit = (e) => {
        e?.preventDefault();
        const trimmed = text.trim();
        if (!trimmed || disabled)
            return;
        onSend(trimmed);
        setText('');
    };
    const onKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submit();
        }
    };
    return (_jsxs("form", { className: "chat-input", onSubmit: submit, children: [_jsxs("div", { className: "editor", children: [_jsx("textarea", { ref: textareaRef, value: text, onChange: (e) => setText(e.target.value), onKeyDown: onKeyDown, placeholder: "Ask anything\u2026", disabled: disabled, rows: 1 }), _jsxs("div", { className: "editor-meta", children: [_jsxs("span", { className: "hint", children: [_jsx("kbd", { children: "Enter" }), " to send \u00B7 ", _jsx("kbd", { children: "Shift" }), "+", _jsx("kbd", { children: "Enter" }), " for newline"] }), _jsxs("span", { className: "hint", children: [text.length.toLocaleString(), " chars"] })] })] }), _jsxs("button", { type: "submit", className: "send", disabled: disabled || !text.trim(), children: ["Send ", _jsx("span", { "aria-hidden": "true", children: "\u2192" })] })] }));
}
