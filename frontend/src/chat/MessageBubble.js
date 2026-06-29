import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
function pad(n, w = 2) {
    return String(n).padStart(w, '0');
}
export function MessageBubble({ msg, index = 0 }) {
    const anchor = `[${pad(index + 1)}]`;
    return (_jsxs("div", { className: `bubble bubble-${msg.role}`, children: [_jsx("span", { className: "anchor", children: anchor }), _jsx("div", { className: "role", children: msg.role === 'user' ? 'You' : msg.role === 'assistant' ? 'Assistant' : msg.role }), msg.content && _jsx("div", { className: "content", children: msg.content }), msg.tool_calls && msg.tool_calls.length > 0 && (_jsx("div", { className: "tool-calls", children: msg.tool_calls.map((tc) => (_jsxs("code", { children: [tc.name, "(", _jsx("span", { className: "arg", children: JSON.stringify(tc.args) }), ")"] }, tc.id))) }))] }));
}
