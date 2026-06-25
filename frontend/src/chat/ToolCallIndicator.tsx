export function ToolCallIndicator({ active }: { active: string[] }) {
  if (active.length === 0) return null;
  return (
    <div className="tool-indicator">
      {active.map((name, i) => (
        <span key={i} className="pill">{name}…</span>
      ))}
    </div>
  );
}
