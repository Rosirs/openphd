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
    // Phase 2: simple validation - composite tool just needs ≥ 1 atomic sub-tool
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
    setSavedMessage(`Saved as "${toolId}". Switch to Chat to use it.`);
    // Refresh tool list
    api.listTools(userId).then(setTools).catch(console.error);
  };

  return (
    <div className="tool-builder-canvas">
      <h2>Custom Tool Builder</h2>
      <p className="info">
        Drag (click) tools from the shelf to compose a custom tool. When you save,
        it becomes available in Chat for the LLM to call. The composite tool runs
        its own LLM loop with the listed sub-tools.
      </p>

      {savedMessage && <div className="chat-error" style={{ color: '#8f8' }}>{savedMessage}</div>}

      <div style={{ display: 'flex', gap: 16, flex: 1, overflow: 'hidden' }}>
        <div style={{ flex: '0 0 240px', overflowY: 'auto' }}>
          <h3 style={{ fontSize: '0.9em' }}>Tools ({atomicTools.length})</h3>
          {atomicTools.map(t => (
            <button
              key={t.name}
              data-testid={`add-${t.name}`}
              onClick={() => addTool(t.name)}
              style={{
                display: 'block', width: '100%', textAlign: 'left',
                padding: '6px 8px', marginBottom: 4,
                background: '#1a1a1a', color: '#fff', border: '1px solid #333',
                borderRadius: 3, cursor: 'pointer', fontSize: '0.85em',
              }}
            >
              <div>{t.name}</div>
              <div style={{ color: '#888', fontSize: '0.8em' }}>{t.category}</div>
            </button>
          ))}
        </div>

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ fontSize: '0.9em' }}>Sub-pipeline</h3>
          <div
            style={{
              flex: 1, background: '#0a0a0a', border: '1px solid #222',
              borderRadius: 4, padding: 8, overflowY: 'auto',
            }}
          >
            {pipeline.length === 0 && (
              <div style={{ color: '#666' }}>Click tools on the left to add.</div>
            )}
            {pipeline.map((id, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  padding: 8, background: '#1a1a1a', borderRadius: 4, marginBottom: 4,
                }}
              >
                <span style={{ color: '#888' }}>{idx + 1}.</span>
                <span style={{ flex: 1 }}>{id}</span>
                <button
                  onClick={() => removeTool(idx)}
                  style={{
                    background: 'transparent', color: '#f88',
                    border: '1px solid #633', borderRadius: 3, padding: '2px 8px',
                    cursor: 'pointer',
                  }}
                >×</button>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
            <button
              data-testid="save-btn"
              disabled={!validation.valid}
              onClick={() => setShowModal(true)}
              style={{
                padding: '8px 16px',
                background: validation.valid ? '#43a047' : '#555',
                color: '#fff', border: 'none', borderRadius: 4,
                cursor: validation.valid ? 'pointer' : 'not-allowed',
              }}
            >
              Save as my tool
            </button>
          </div>
        </div>
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
