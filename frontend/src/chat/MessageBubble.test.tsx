import { render, screen } from '@testing-library/react';
import { MessageBubble } from './MessageBubble';
import type { Message } from '../api/types';

test('renders user content', () => {
  const msg: Message = { role: 'user', content: 'hello', timestamp: '2026-06-25T12:00:00Z' };
  render(<MessageBubble msg={msg} />);
  expect(screen.getByText('hello')).toBeInTheDocument();
});

test('renders tool calls', () => {
  const msg: Message = {
    role: 'assistant', timestamp: '2026-06-25T12:00:00Z',
    tool_calls: [{ id: 'tc1', name: 'arxiv_search', args: { q: 'ML' } }],
  };
  render(<MessageBubble msg={msg} />);
  expect(screen.getByText(/arxiv_search/)).toBeInTheDocument();
});
