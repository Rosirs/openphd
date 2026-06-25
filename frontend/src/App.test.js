import { jsx as _jsx } from "react/jsx-runtime";
import { render, screen } from '@testing-library/react';
import App from './App';
test('renders chat tab by default', async () => {
    render(_jsx(App, {}));
    // Both tab buttons should be present
    expect(screen.getByRole('button', { name: /Chat/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Canvas/i })).toBeInTheDocument();
    // Chat input should be present
    expect(screen.getByPlaceholderText(/Ask anything/i)).toBeInTheDocument();
});
