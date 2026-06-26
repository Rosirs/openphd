export type Category = 'academic' | 'writing' | 'admin' | 'mock' | 'composite';

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

export interface ToolSpec {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  category: Category;
}

export interface ToolCall {
  id: string;
  name: string;
  args: Record<string, unknown>;
}

export interface Message {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content?: string | null;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
  name?: string;
  timestamp: string;
}

export interface ChatSession {
  user_id: string;
  conversation_id: string;
  title: string;
  messages: Message[];
  status: 'active' | 'archived';
  created_at: string;
  updated_at: string;
}

export interface CompositeToolDefinition {
  tool_id: string;
  name: string;
  description: string;
  system_prompt: string;
  sub_tools: string[];
  owner_user_id: string;
}

export interface SseToolEvent {
  type: string;
  name?: string;
  args?: Record<string, unknown>;
  content?: string;
  summary?: string;
  success?: boolean;
  run_id?: string;
  message?: string;
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

// Onboard (LLM configuration wizard)
export interface ProviderInfo {
  key: string;
  label: string;
  supported: boolean;
}

export interface ProfileInfo {
  llm_provider: string;
  base_url: string;
  model_name: string;
  api_key_masked: string;
  onboarded: boolean;
}

export interface OnboardStatus {
  configured: boolean;
  onboarded: boolean;
  profile: ProfileInfo | null;
  providers: ProviderInfo[];
}

export interface SaveProfileBody {
  llm_provider: string;
  base_url?: string;
  api_key?: string;
  model_name?: string;
}

export interface TestResponse {
  ok: boolean;
  message: string;
  latency_ms: number;
  model?: string;
}
