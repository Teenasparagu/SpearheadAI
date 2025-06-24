import React, { useEffect, useState } from 'react';

function GameViewer() {
  const [state, setState] = useState(null);
  const [messages, setMessages] = useState([]);
  const [prompt, setPrompt] = useState('');
  const [inputValue, setInputValue] = useState('');

  const fetchState = () => {
    fetch('/api/state')
      .then(res => res.json())
      .then(data => setState(data));
  };

  const fetchMessages = () => {
    fetch('/api/messages')
      .then(res => res.json())
      .then(list => {
        if (list.length === 0) return;
        setMessages(prev => {
          const updated = [...prev];
          list.forEach(m => {
            if (m.type === 'prompt') {
              setPrompt(m.text);
            } else if (m.type === 'log') {
              updated.push(m.text);
            }
          });
          return updated;
        });
      });
  };

  useEffect(() => {
    fetchState();
    const id1 = setInterval(fetchState, 5000);
    const id2 = setInterval(fetchMessages, 1000);
    return () => { clearInterval(id1); clearInterval(id2); };
  }, []);

  const startDeployment = () => {
    fetch('/api/start_deployment', { method: 'POST' });
  };

  const sendAnswer = () => {
    fetch('/api/answer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answer: inputValue })
    }).then(() => setInputValue(''));
  };

  const handleCellClick = (x, y) => {
    setInputValue(`${x} ${y}`);
  };

  if (!state) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <div style={{ position: 'absolute', top: 10, right: 10 }}>
        <button onClick={startDeployment}>Start Deployment</button>
        <form method="GET" action="/reset" style={{ display: 'inline-block', marginLeft: '10px' }}>
          <button type="submit" style={{ backgroundColor: 'darkred', color: 'white' }}>Reset Game</button>
        </form>
      </div>
      <h1 style={{ textAlign: 'center' }}>Spearhead AI – Game Grid</h1>
      <table className="grid">
        <thead>
          <tr>
            <th></th>
            {state.grid[0].map((_, x) => <th key={x} className="coord">{x}</th>)}
          </tr>
        </thead>
        <tbody>
          {state.grid.map((row, y) => (
            <tr key={y}>
              <th className="coord">{y}</th>
              {row.map((cell, x) => (
                <td
                  key={x}
                  style={{ backgroundColor: cell.color, color: ['black','#0044cc','#cc0000'].includes(cell.color) ? 'white' : 'black' }}
                  onClick={() => handleCellClick(x, y)}
                >
                  {cell.label}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {prompt && (
        <div style={{ textAlign: 'center', marginTop: '20px' }}>
          <div><strong>{prompt}</strong></div>
          <input type="text" value={inputValue} onChange={e => setInputValue(e.target.value)} />
          <button onClick={sendAnswer}>Send</button>
        </div>
      )}
      <div className="messages">
        <h2>Game Log</h2>
        <ul>
          {messages.map((msg, idx) => <li key={idx}>{msg}</li>)}
        </ul>
      </div>
    </div>
  );
}

ReactDOM.render(<GameViewer />, document.getElementById('root'));
