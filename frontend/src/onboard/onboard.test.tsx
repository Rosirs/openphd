import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProviderPicker } from './ProviderPicker';
import { LLMConfigForm } from './LLMConfigForm';
import type { ProviderInfo } from '../api/types';

const providers: ProviderInfo[] = [
  { key: 'openai', label: 'OpenAI', supported: true },
  { key: 'anthropic', label: 'Anthropic', supported: false },
];

test('renders all providers', () => {
  render(<ProviderPicker providers={providers} value="openai" onChange={() => {}} />);
  expect(screen.getByRole('option', { name: /OpenAI/ })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: /Anthropic/ })).toBeInTheDocument();
});

test('anthropic option is disabled', () => {
  render(<ProviderPicker providers={providers} value="openai" onChange={() => {}} />);
  const opt = screen.getByRole('option', { name: /Anthropic/ }) as HTMLOptionElement;
  expect(opt.disabled).toBe(true);
});

test('selecting provider autofills base_url and model', async () => {
  const user = userEvent.setup();
  render(
    <LLMConfigForm
      providers={[
        { key: 'openai', label: 'OpenAI', supported: true },
        { key: 'deepseek', label: 'DeepSeek', supported: true },
      ]}
      onSave={() => {}}
      onCancel={() => {}}
    />
  );
  const select = screen.getByTestId('provider-picker') as HTMLSelectElement;
  await user.selectOptions(select, 'deepseek');
  const baseUrl = screen.getByTestId('base-url') as HTMLInputElement;
  const model = screen.getByTestId('model-name') as HTMLInputElement;
  expect(baseUrl.value).toContain('deepseek');
  expect(model.value).toBe('deepseek-chat');
});