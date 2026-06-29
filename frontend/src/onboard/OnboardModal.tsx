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
            <h2>Welcome to your <em>desk</em>.</h2>
            <p>
              PhD-Agent calls tools on your behalf — arxiv, email drafts, prose
              polish, PDF summaries. To make this feel like <em>your</em> work,
              wire up an LLM.
            </p>
            <p className="hint">
              No API key handy? Skip to use the built-in mock LLM. You can
              change this any time from the gear in the header.
            </p>
            <div className="actions">
              <button className="btn" onClick={handleSkip} disabled={skipping} data-testid="skip-btn">
                {skipping ? 'Skipping…' : 'Skip (use mock)'}
              </button>
              <button className="btn btn-primary" onClick={() => setStep('form')} data-testid="setup-btn">
                Setup LLM
              </button>
            </div>
          </>
        ) : (
          <>
            <h2>Configure your <em>model</em></h2>
            <p className="hint">
              Pick a provider, drop in your key, then test the connection. The
              key stays on the server — only a masked preview is shown.
            </p>
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
