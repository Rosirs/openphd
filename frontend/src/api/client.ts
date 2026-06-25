import type { AgentContract, RunResponse } from './types';

const BASE = '/api';

export const apiClient = {
  async catalog(): Promise<AgentContract[]> {
    const r = await fetch(`${BASE}/agents/catalog`);
    if (!r.ok) throw new Error(`catalog failed: ${r.status}`);
    const body = await r.json();
    return body.agents;
  },

  async runPipeline(payload: {
    user_id: string;
    active_pipeline: string[];
    dynamic_storage?: Record<string, unknown>;
  }): Promise<RunResponse> {
    const r = await fetch(`${BASE}/pipelines/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!r.ok) throw new Error(`run failed: ${r.status}`);
    return r.json();
  },
};
