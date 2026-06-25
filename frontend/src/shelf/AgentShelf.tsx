import type { AgentContract, Category } from '../api/types';
import { AgentCard } from './AgentCard';

interface Props {
  contracts: AgentContract[];
  onDragStart: (agentId: string) => void;
}

const CATEGORY_ORDER: Category[] = ['academic', 'writing', 'admin', 'mock'];

export function AgentShelf({ contracts, onDragStart }: Props) {
  const grouped = CATEGORY_ORDER.map(cat => ({
    cat,
    items: contracts.filter(c => c.category === cat),
  })).filter(g => g.items.length > 0);

  return (
    <aside style={{ width: 240, padding: 12, borderRight: '1px solid #333', overflowY: 'auto' }}>
      <h3 style={{ margin: '0 0 12px' }}>Agent Shelf</h3>
      {grouped.map(g => (
        <div key={g.cat} style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, textTransform: 'uppercase', color: '#888', marginBottom: 6 }}>
            {g.cat}
          </div>
          {g.items.map(c => (
            <AgentCard key={c.agent_id} contract={c} onDragStart={onDragStart} />
          ))}
        </div>
      ))}
    </aside>
  );
}
