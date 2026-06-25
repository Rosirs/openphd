import { useState, useEffect } from 'react';
import { api } from '../api/client';

export function SaveToolModal({
  subTools, onSave, onClose,
}: {
  subTools: string[];
  onSave: (data: { tool_id: string; name: string; system_prompt: string }) => void;
  onClose: () => void;
}) {
  const [toolId, setToolId] = useState('');
  const [name, setName] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [preview, setPreview] = useState<string>('');

  useEffect(() => {
    if (name || systemPrompt) {
      api.previewPrompt(name || 'Tool', systemPrompt, subTools)
        .then(setPreview)
        .catch(() => setPreview(''));
    }
  }, [name, systemPrompt, subTools]);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Save as my tool</h2>
        <label>
          Tool ID (unique, lowercase)
          <input
            data-testid="tool-id"
            value={toolId}
            onChange={(e) => setToolId(e.target.value.replace(/[^a-z0-9_]/g, '_'))}
            placeholder="my_research_finder"
          />
        </label>
        <label>
          Name
          <input
            data-testid="tool-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="My Research Finder"
          />
        </label>
        <label>
          System Prompt (your intent — what should this tool do?)
          <textarea
            data-testid="tool-prompt"
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            placeholder="Search arxiv for recent papers and polish the summary."
          />
        </label>
        <p className="sub-tools">Sub-tools: {subTools.join(', ')}</p>
        {preview && (
          <details>
            <summary style={{ cursor: 'pointer', color: '#8cf' }}>Preview augmented prompt</summary>
            <pre style={{
              background: '#000', padding: 8, fontSize: '0.8em',
              whiteSpace: 'pre-wrap', maxHeight: 200, overflowY: 'auto',
            }}>{preview}</pre>
          </details>
        )}
        <div className="actions">
          <button onClick={onClose}>Cancel</button>
          <button
            data-testid="modal-save"
            disabled={!toolId || !name}
            onClick={() => onSave({ tool_id: toolId, name, system_prompt: systemPrompt })}
          >Save</button>
        </div>
      </div>
    </div>
  );
}
