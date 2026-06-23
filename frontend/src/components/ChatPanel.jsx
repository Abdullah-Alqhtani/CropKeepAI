/*
 * Follow-up chat panel for the currently selected diagnosis.
 * It sends a question with the diagnosis ID so the backend can build relevant AI context.
 */
import { useState } from 'react';
import { Bot, Send, UserRound } from 'lucide-react';
import { api } from '../services/api.js';

export function ChatPanel({ diagnosisId }) {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function submit(event) {
    // Replace local messages with the server's ordered session history after each reply.
    event.preventDefault();
    if (!message.trim()) return;
    setError('');
    setLoading(true);
    try {
      const result = await api.chat(diagnosisId, message);
      setMessages(result.messages);
      setMessage('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel chat-panel">
      <div className="panel-title">
        <Bot size={20} />
        <h2>Follow-up Chat</h2>
      </div>
      <div className="message-list">
        {messages.length === 0 && <p className="muted">Ask about severity, spread risk, treatment timing, or best practices.</p>}
        {messages.map((item) => (
          <article className={`message ${item.role}`} key={item.id}>
            {item.role === 'user' ? <UserRound size={16} /> : <Bot size={16} />}
            <p>{item.content}</p>
          </article>
        ))}
      </div>
      <form className="chat-form" onSubmit={submit}>
        <input value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Ask a follow-up question" />
        <button className="icon-button strong" disabled={loading} title="Send message">
          <Send size={18} />
        </button>
      </form>
      {error && <div className="error-text">{error}</div>}
    </section>
  );
}
