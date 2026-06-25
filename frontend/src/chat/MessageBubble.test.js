import { jsx as _jsx } from "react/jsx-runtime";
import { render, screen } from '@testing-library/react';
import { MessageBubble } from './MessageBubble';
test('renders user content', () => {
    const msg = { role: 'user', content: 'hello', timestamp: '2026-06-25T12:00:00Z' };
    render(_jsx(MessageBubble, { msg: msg }));
    expect(screen.getByText('hello')).toBeInTheDocument();
});
test('renders tool calls', () => {
    const msg = {
        role: 'assistant', timestamp: '2026-06-25T12:00:00Z',
        tool_calls: [{ id: 'tc1', name: 'arxiv_search', args: { q: 'ML' } }],
    };
    render(_jsx(MessageBubble, { msg: msg }));
    expect(screen.getByText(/arxiv_search/)).toBeInTheDocument();
});
