import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export function MessageBubble({ msg }) {
    return (_jsxs("div", { className: `bubble bubble-${msg.role}`, children: [_jsx("div", { className: "role", children: msg.role }), msg.content && _jsx("div", { className: "content", children: msg.content }), msg.tool_calls && msg.tool_calls.length > 0 && (_jsx("div", { className: "tool-calls", children: msg.tool_calls.map((tc) => (_jsxs("code", { children: [tc.name, "(", JSON.stringify(tc.args), ")"] }, tc.id))) }))] }));
}
