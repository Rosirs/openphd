export type Category = 'academic' | 'writing' | 'admin' | 'mock';

export interface AgentContract {
  agent_id: string;
  name: string;
  description: string;
  category: Category;
  required_fields: string[];
  output_fields: string[];
  token_budget: number;
  isolation: 'in_process';
}

export interface StepValidation {
  step: number;
  agent_id: string;
  required: string[];
  provided_at_step: string[];
  missing: string[];
  ok: boolean;
}

export interface ValidationResult {
  valid: boolean;
  failed_at: number | null;
  steps: StepValidation[];
}

export interface RunResponse {
  run_id: string;
  status: 'running' | 'completed' | 'partial' | 'failed';
}

export interface SseEvent {
  step: number;
  agent_id: string;
  status: string;
  duration_ms: number;
  error: string | null;
  output?: Record<string, unknown>;
}
