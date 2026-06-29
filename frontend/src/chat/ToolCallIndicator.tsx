export function ToolCallIndicator({ active }: { active: string[] }) {
  if (active.length === 0) return null;
  return (
    <div className="tool-indicator" role="status" aria-live="polite">
      {active.map((name, i) => (
        <span key={`${name}-${i}`} className="pill">
          <span className="dot" />
          {name}
        </span>
      ))}
    </div>
  );
}
