const { useState, useEffect } = React;

function GameViewer() {
  const [state, setState] = useState(null);

  const fetchState = () => {
    fetch('/api/state')
      .then(res => res.json())
      .then(data => setState(data));
  };

  useEffect(() => {
    fetchState();
    const id = setInterval(fetchState, 10000); // refresh every 10s
    return () => clearInterval(id);
  }, []);

  if (!state) return React.createElement('div', null, 'Loading...');

  const gridRows = state.grid.map((row, y) =>
    React.createElement('tr', { key: y }, [
      React.createElement('th', { key: 'th' + y, className: 'coord' }, y),
      ...row.map((cell, x) =>
        React.createElement('td', {
          key: x,
          style: { backgroundColor: cell.color, color: ['black','#0044cc','#cc0000'].includes(cell.color) ? 'white' : 'black' }
        }, cell.label)
      )
    ])
  );

  const headerRow = React.createElement('tr', null, [
    React.createElement('th', { key: 'corner' }, ''),
    ...state.grid[0].map((_, x) => React.createElement('th', { key: x, className: 'coord' }, x))
  ]);

  const table = React.createElement('table', { className: 'grid' }, [headerRow, ...gridRows]);

  const logItems = state.messages.map((msg, idx) => React.createElement('li', { key: idx }, msg));

  const resetButton = React.createElement('form', { method: 'GET', action: '/reset', style: { position: 'absolute', top: 10, right: 10 } },
    React.createElement('button', { type: 'submit', style: { backgroundColor: 'darkred', color: 'white' } }, 'Reset Game')
  );

  const messagesDiv = React.createElement('div', { className: 'messages' }, [
    React.createElement('h2', { key: 'title' }, 'Game Log'),
    React.createElement('ul', { key: 'list' }, logItems)
  ]);

  return React.createElement(React.Fragment, null, [
    resetButton,
    React.createElement('h1', { style: { textAlign: 'center' } }, 'Spearhead AI – Game Grid'),
    table,
    messagesDiv
  ]);
}

ReactDOM.render(React.createElement(GameViewer), document.getElementById('root'));
