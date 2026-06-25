import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { ChatView } from './chat/ChatView';
import { ToolBuilderCanvas } from './canvas/ToolBuilderCanvas';
import './App.css';
export default function App() {
    const [tab, setTab] = useState('chat');
    const userId = 'default-user';
    return (_jsxs("div", { className: "app", children: [_jsxs("header", { className: "tabs", children: [_jsx("button", { className: tab === 'chat' ? 'active' : '', onClick: () => setTab('chat'), children: "Chat" }), _jsx("button", { className: tab === 'canvas' ? 'active' : '', onClick: () => setTab('canvas'), children: "Canvas" })] }), _jsxs("main", { children: [tab === 'chat' && _jsx(ChatView, { userId: userId }), tab === 'canvas' && _jsx(ToolBuilderCanvas, { userId: userId })] })] }));
}
