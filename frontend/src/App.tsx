import { useEffect, useState } from 'react';
import { AgentShelf } from './shelf/AgentShelf';
import { FlowCanvas } from './canvas/FlowCanvas';
import { WorkspaceRoot } from './workspace/WorkspaceRoot';
import { apiClient } from './api/client';
import type { AgentContract, SseEvent } from './api/types';

export default function App() {
  const [contracts, setContracts] = useState<AgentContract[]>([]);
  const [events, setEvents] = useState<SseEvent[]>([]);
  const [finalData, setFinalData] = useState<Record<string, unknown>>({});
  const [activatedAgents, setActivatedAgents] = useState<string[]>([]);

  useEffect(() => {
    apiClient.catalog().then(setContracts).catch(console.error);
  }, []);

  const onRun = async (pipeline: string[]) => {
    setEvents([]);
    setFinalData({});
    setActivatedAgents(pipeline);
    try {
      const result = await apiClient.runPipeline({
        user_id: 'demo-user',
        active_pipeline: pipeline,
        dynamic_storage: { echo_input: 'hello from frontend' },
      });
      setFinalData({ run_id: result.run_id, status: result.status });
    } catch (e) {
      console.error(e);
    }
  };

  if (contracts.length === 0) {
    return <div style={{ padding: 24 }}>Loading agent catalog…</div>;
  }

  return (
    <div style={{ display: 'flex', height: '100vh', color: '#fff', background: '#0a0a0a' }}>
      <AgentShelf contracts={contracts} onDragStart={() => {}} />
      <FlowCanvas contracts={contracts} onRun={onRun} />
      <WorkspaceRoot
        activatedAgents={activatedAgents}
        contracts={contracts}
        events={events}
        finalData={finalData}
      />
    </div>
  );
}
