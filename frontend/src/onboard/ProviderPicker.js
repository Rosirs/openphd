import { jsx as _jsx } from "react/jsx-runtime";
export function ProviderPicker({ providers, value, onChange, }) {
    return (_jsx("select", { "data-testid": "provider-picker", value: value, onChange: (e) => onChange(e.target.value), children: providers.map((p) => (_jsx("option", { value: p.key, disabled: !p.supported, children: p.supported ? p.label : `${p.label} (coming soon)` }, p.key))) }));
}
