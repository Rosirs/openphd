import type { AgentContract, SseEvent } from '../api/types';
import { PipelineRunLog } from './PipelineRunLog';
import { MockWidget } from './MockWidget';

interface Props {
  activatedAgents: string[];
  contracts: AgentContract[];
  events: SseEvent[];
  finalData: Record<string, unknown>;
}

export function WorkspaceRoot({ activatedAgents, contracts, events, finalData }: Props) {
  return (
    <aside
      style={{
        width: 360,
        padding: 12,
        borderLeft: '1px solid #333',
        overflowY: 'auto',
        background: '#0e0e0e',
      }}
    >
      <h3 style={{ margin: '0 0 12px' }}>Workspace</h3>
      <PipelineRunLog events={events} />
      {activatedAgents.map(id => {
        const c = contracts.find(x => x.agent_id === id);
        return c ? <MockWidget key={id} agentId={id} data={finalData} /> : null;
      })}
    </aside>
  );
}
