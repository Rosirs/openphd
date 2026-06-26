import type { OnboardStatus, SaveProfileBody, TestResponse } from '../api/types';
import { LLMConfigForm } from './LLMConfigForm';

export function SettingsModal({
  status, onClose, onSave, onTest,
}: {
  status: OnboardStatus;
  onClose: () => void;
  onSave: (data: SaveProfileBody) => Promise<void> | void;
  onTest: (data: SaveProfileBody) => Promise<TestResponse>;
}) {
  return (
    <div className="modal-backdrop" data-testid="settings-modal" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>LLM Settings</h2>
        {status.profile ? (
          <p className="hint">
            Current: <strong>{status.profile.llm_provider}</strong> · {status.profile.model_name}
            <br />
            Key: <code>{status.profile.api_key_masked}</code>
          </p>
        ) : (
          <p className="hint">No LLM configured yet (using mock).</p>
        )}
        <LLMConfigForm
          providers={status.providers}
          initial={status.profile ? {
            llm_provider: status.profile.llm_provider,
            base_url: status.profile.base_url,
            model_name: status.profile.model_name,
          } : undefined}
          onSave={async (data) => { await onSave(data); onClose(); }}
          onCancel={onClose}
          onTest={onTest}
        />
      </div>
    </div>
  );
}