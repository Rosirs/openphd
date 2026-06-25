import { useState } from 'react';
import { ChatView } from './chat/ChatView';
import { ToolBuilderCanvas } from './canvas/ToolBuilderCanvas';
import './App.css';

type Tab = 'chat' | 'canvas';

export default function App() {
  const [tab, setTab] = useState<Tab>('chat');
  const userId = 'default-user';

  return (
    <div className="app">
      <header className="tabs">
        <button
          className={tab === 'chat' ? 'active' : ''}
          onClick={() => setTab('chat')}
        >Chat</button>
        <button
          className={tab === 'canvas' ? 'active' : ''}
          onClick={() => setTab('canvas')}
        >Canvas</button>
      </header>
      <main>
        {tab === 'chat' && <ChatView userId={userId} />}
        {tab === 'canvas' && <ToolBuilderCanvas userId={userId} />}
      </main>
    </div>
  );
}
