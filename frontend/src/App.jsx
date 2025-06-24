import { useEffect, useState } from 'react';

function App() {
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetch('http://127.0.0.1:5000/api/hello')
      .then(res => res.json())
      .then(data => setMessage(data.message));
  }, []);

  return (
    <div>
      <h1>COMP9900 HDingo project</h1>
      <p>Message from Backend (python flask): {message}</p>
    </div>
  );
}

export default App;
