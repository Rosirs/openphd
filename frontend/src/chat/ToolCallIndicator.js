import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
export function ToolCallIndicator({ active }) {
    if (active.length === 0)
        return null;
    return (_jsx("div", { className: "tool-indicator", children: active.map((name, i) => (_jsxs("span", { className: "pill", children: [name, "\u2026"] }, i))) }));
}
