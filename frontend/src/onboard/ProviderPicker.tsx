import type { ProviderInfo } from '../api/types';

export function ProviderPicker({
  providers, value, onChange,
}: {
  providers: ProviderInfo[];
  value: string;
  onChange: (key: string) => void;
}) {
  return (
    <select data-testid="provider-picker" value={value} onChange={(e) => onChange(e.target.value)}>
      {providers.map((p) => (
        <option key={p.key} value={p.key} disabled={!p.supported}>
          {p.supported ? p.label : `${p.label} (coming soon)`}
        </option>
      ))}
    </select>
  );
}