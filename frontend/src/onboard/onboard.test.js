import { jsx as _jsx } from "react/jsx-runtime";
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProviderPicker } from './ProviderPicker';
import { LLMConfigForm } from './LLMConfigForm';
const providers = [
    { key: 'openai', label: 'OpenAI', supported: true },
    { key: 'anthropic', label: 'Anthropic', supported: false },
];
test('renders all providers', () => {
    render(_jsx(ProviderPicker, { providers: providers, value: "openai", onChange: () => { } }));
    expect(screen.getByRole('option', { name: /OpenAI/ })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /Anthropic/ })).toBeInTheDocument();
});
test('anthropic option is disabled', () => {
    render(_jsx(ProviderPicker, { providers: providers, value: "openai", onChange: () => { } }));
    const opt = screen.getByRole('option', { name: /Anthropic/ });
    expect(opt.disabled).toBe(true);
});
test('selecting provider autofills base_url and model', async () => {
    const user = userEvent.setup();
    render(_jsx(LLMConfigForm, { providers: [
            { key: 'openai', label: 'OpenAI', supported: true },
            { key: 'deepseek', label: 'DeepSeek', supported: true },
        ], onSave: () => { }, onCancel: () => { } }));
    const select = screen.getByTestId('provider-picker');
    await user.selectOptions(select, 'deepseek');
    const baseUrl = screen.getByTestId('base-url');
    const model = screen.getByTestId('model-name');
    expect(baseUrl.value).toContain('deepseek');
    expect(model.value).toBe('deepseek-chat');
});
test('selecting MiniMax autofills MiniMax base_url and model', async () => {
    const user = userEvent.setup();
    render(_jsx(LLMConfigForm, { providers: [
            { key: 'openai', label: 'OpenAI', supported: true },
            { key: 'MiniMax', label: 'MiniMax', supported: true },
        ], onSave: () => { }, onCancel: () => { } }));
    const select = screen.getByTestId('provider-picker');
    await user.selectOptions(select, 'MiniMax');
    const baseUrl = screen.getByTestId('base-url');
    const model = screen.getByTestId('model-name');
    expect(baseUrl.value).toBe('https://api.MiniMax.chat/v1');
    expect(model.value).toBe('MiniMax-M3');
});
