import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import App from './App';

vi.mock('./api/client', () => ({
  api: {
    createConversation: vi.fn(() => Promise.resolve({
      conversation_id: 'c1', user_id: 'default-user', title: 'New chat',
      messages: [], status: 'active', created_at: '', updated_at: '',
    })),
    subscribeMessages: vi.fn(() => ({
      stream: (async function* () { /* noop */ })(),
      close: vi.fn(),
    })),
    listTools: vi.fn(() => Promise.resolve([])),
  },
  onboardApi: {
    getStatus: vi.fn(() => Promise.resolve({
      configured: true, onboarded: true, profile: {
        llm_provider: 'openai', base_url: 'https://api.openai.com/v1',
        model_name: 'gpt-4o-mini', api_key_masked: 'sk-...1234', onboarded: true,
      },
      providers: [{ key: 'openai', label: 'OpenAI', supported: true }],
    })),
    save: vi.fn(() => Promise.resolve({ profile: { api_key_masked: 'sk-...1234' } })),
    test: vi.fn(() => Promise.resolve({ ok: true, message: 'connected', latency_ms: 100 })),
    skip: vi.fn(() => Promise.resolve({ ok: true })),
  },
}));

test('renders chat and canvas tabs after loading', async () => {
  render(<App />);
  expect(screen.getByText(/Loading/i)).toBeInTheDocument();
  await waitFor(() => {
    expect(screen.getByRole('button', { name: /Chat/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Canvas/i })).toBeInTheDocument();
  });
  await waitFor(() => {
    expect(screen.getByPlaceholderText(/Ask anything/i)).toBeInTheDocument();
  });
});