import { useState } from 'react';
import type { ProviderInfo, SaveProfileBody, TestResponse } from '../api/types';
import { LLMConfigForm } from './LLMConfigForm';

export function OnboardModal({
  providers, onSkip, onSave, onTest,
}: {
  providers: ProviderInfo[];
  onSkip: () => Promise<void> | void;
  onSave: (data: SaveProfileBody) => Promise<void> | void;
  onTest: (data: SaveProfileBody) => Promise<TestResponse>;
}) {
  const [step, setStep] = useState<'welcome' | 'form'>('welcome');
  const [skipping, setSkipping] = useState(false);

  const handleSkip = async () => {
    setSkipping(true);
    try {
      await onSkip();
    } finally {
      setSkipping(false);
    }
  };

  return (
    <div className="modal-backdrop" data-testid="onboard-modal">
      <div className="modal">
        {step === 'welcome' ? (
          <>
            <h2>Welcome to PhD-Agent</h2>
            <p>Configure your LLM to start chatting with the AI assistant.</p>
            <p className="hint">
              No API key? Skip to use the local mock LLM (you can configure later).
            </p>
            <div className="actions">
              <button data-testid="setup-btn" onClick={() => setStep('form')}>
                Setup LLM
              </button>
              <button data-testid="skip-btn" onClick={handleSkip} disabled={skipping}>
                {skipping ? 'Skipping...' : 'Skip (use mock)'}
              </button>
            </div>
          </>
        ) : (
          <>
            <h2>LLM Setup</h2>
            <LLMConfigForm
              providers={providers}
              onSave={onSave}
              onCancel={() => setStep('welcome')}
              onTest={onTest}
            />
          </>
        )}
      </div>
    </div>
  );
}