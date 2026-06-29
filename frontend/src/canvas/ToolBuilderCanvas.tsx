import { useEffect, useMemo, useState } from 'react';
import { api } from '../api/client';
import { SaveToolModal } from './SaveToolModal';
import type { ToolSpec } from '../api/types';

interface Props { userId: string; }

export function ToolBuilderCanvas({ userId }: Props) {
  const [tools, setTools] = useState<ToolSpec[]>([]);
  const [pipeline, setPipeline] = useState<string[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    api.listTools(userId).then(setTools).catch(console.error);
  }, [userId]);

  const toolMap = useMemo(
    () => new Map(tools.map(t => [t.name, t])), [tools],
  );

  const atomicTools = tools.filter(t => t.category !== 'composite');

  const validation = useMemo(() => {
    if (pipeline.length === 0) return { valid: false, reason: 'empty' };
    for (const id of pipeline) {
      if (!toolMap.has(id)) return { valid: false, reason: `unknown tool: ${id}` };
    }
    return { valid: true, reason: '' };
  }, [pipeline, toolMap]);

  const addTool = (id: string) => setPipeline(p => [...p, id]);
  const removeTool = (idx: number) => setPipeline(p => p.filter((_, i) => i !== idx));

  const handleSaved = (toolId: string) => {
    setShowModal(false);
    setPipeline([]);
    setSavedMessage(`Saved "${toolId}" — switch to Chat to use it.`);
    api.listTools(userId).then(setTools).catch(console.error);
  };

  return (
    <div className="canvas-view">
      <div className="canvas-intro">
        <div className="eyebrow">The workshop</div>
        <h2>Compose your <em>own</em> tool</h2>
        <p>
          Pick atomic tools from the shelf, chain them in order, then add a system
          prompt that names their purpose. The composite runs its own LLM loop
          and is callable from Chat like any other tool.
        </p>
      </div>

      <div className="canvas-body">
        <aside className="shelf">
          <h3>
            <span>Shelf</span>
            <span className="count">{atomicTools.length}</span>
          </h3>
          {atomicTools.length === 0 && (
            <p className="hint" style={{ fontStyle: 'italic' }}>No tools loaded.</p>
          )}
          {atomicTools.map(t => (
            <button
              key={t.name}
              data-testid={`add-${t.name}`}
              onClick={() => addTool(t.name)}
              className="tool-card"
            >
              <div className="name">{t.name}</div>
              <span className="cat">{t.category}</span>
            </button>
          ))}
        </aside>

        <section className="board">
          <h3>Sub-pipeline</h3>
          {pipeline.length === 0 ? (
            <div className="pipeline-empty">
              <div className="glyph">※</div>
              <div>Click tools on the shelf to add them here.</div>
            </div>
          ) : (
            <div className="pipeline">
              {pipeline.map((id, idx) => {
                const t = toolMap.get(id);
                return (
                  <div key={`${id}-${idx}`} className="pipeline-step">
                    <span className="num">{String(idx + 1).padStart(2, '0')}</span>
                    <span className="name">{id}</span>
                    {t && <span className="cat">{t.category}</span>}
                    <button
                      className="remove"
                      onClick={() => removeTool(idx)}
                      aria-label={`Remove ${id}`}
                      title="Remove"
                    >×</button>
                  </div>
                );
              })}
            </div>
          )}

          <div className="canvas-actions">
            <button
              data-testid="save-btn"
              className="btn btn-primary"
              disabled={!validation.valid}
              onClick={() => setShowModal(true)}
            >
              Save as my tool
            </button>
            {savedMessage && (
              <span className="save-status">
                <span aria-hidden="true">●</span>
                {savedMessage}
              </span>
            )}
          </div>
        </section>
      </div>

      {showModal && (
        <SaveToolModal
          subTools={pipeline}
          onClose={() => setShowModal(false)}
          onSave={async (data) => {
            await api.saveComposite(userId, {
              tool_id: data.tool_id,
              name: data.name,
              description: data.system_prompt,
              system_prompt: data.system_prompt,
              sub_tools: pipeline,
            });
            handleSaved(data.tool_id);
          }}
        />
      )}
    </div>
  );
}
