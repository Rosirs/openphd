import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export function ToolCallIndicator({ active }) {
    if (active.length === 0)
        return null;
    return (_jsx("div", { className: "tool-indicator", role: "status", "aria-live": "polite", children: active.map((name, i) => (_jsxs("span", { className: "pill", children: [_jsx("span", { className: "dot" }), name] }, `${name}-${i}`))) }));
}
