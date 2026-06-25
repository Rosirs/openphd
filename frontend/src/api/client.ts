import type { AgentContract, RunResponse, SseEvent } from './types';

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

  subscribeEvents(runId: string, onEvent: (e: SseEvent) => void): () => void {
    const es = new EventSource(`${BASE}/pipelines/${runId}/events`);
    es.onmessage = (msg) => {
      const ev = JSON.parse(msg.data) as SseEvent;
      onEvent(ev);
      if (ev.status === 'end') es.close();
    };
    return () => es.close();
  },
};
