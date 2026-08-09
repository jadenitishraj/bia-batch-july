// The right column: the chatbot. It sends your message to the backend agent, shows the reply,
// and keeps the trace of each reply so the 👁 button can show how the answer was made.

import { useEffect, useRef, useState } from "react";

import { api } from "../api";
import TracePanel from "./TracePanel";

const IDEAS = [
  "What categories do I have?",
  "How many times was I happy?",
  "Add a category called Travel",
];

const WELCOME = { role: "assistant", content: "Hi! Ask me anything about your notes 🌱" };

export default function Chat({ onChanged }) {
  const [messages, setMessages] = useState([WELCOME]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [openTrace, setOpenTrace] = useState(null);
  const bottom = useRef(null);

  // Always keep the newest message in view
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  async function send(message) {
    if (!message.trim() || busy) return;

    // The backend only wants role and content, so leave the traces behind
    const history = messages.map(({ role, content }) => ({ role, content }));
    setMessages([...messages, { role: "user", content: message }]);
    setText("");
    setBusy(true);
    try {
      const { reply, trace } = await api.chat(message, history);
      setMessages((current) => [...current, { role: "assistant", content: reply, trace }]);
      onChanged();
    } catch {
      setMessages((current) => [
        ...current,
        { role: "assistant", content: "I could not reach the server. Is the backend running?" },
      ]);
    }
    setBusy(false);
  }

  return (
    <aside className="chat">
      <header className="chat-head">
        <h2>✨ Assistant</h2>
        <p className="muted">Ask about your notes, or ask me to change them</p>
      </header>

      <div className="chat-body">
        {messages.map((message, index) => (
          <div className={`msg ${message.role}`} key={index}>
            <div className="bubble">{message.content}</div>
            {message.trace && (
              <button
                className="eye-btn"
                title="See how this answer was made"
                onClick={() => setOpenTrace(message.trace)}
              >
                👁
              </button>
            )}
          </div>
        ))}
        {busy && <div className="msg assistant"><div className="bubble typing">thinking…</div></div>}
        <div ref={bottom} />
      </div>

      <div className="ideas">
        {IDEAS.map((idea) => (
          <button key={idea} className="idea" onClick={() => send(idea)}>
            {idea}
          </button>
        ))}
      </div>

      <form
        className="chat-form"
        onSubmit={(event) => {
          event.preventDefault();
          send(text);
        }}
      >
        <input
          placeholder="Ask me something…"
          value={text}
          onChange={(event) => setText(event.target.value)}
        />
        <button className="primary" disabled={busy}>
          Send
        </button>
      </form>

      {openTrace && <TracePanel trace={openTrace} onClose={() => setOpenTrace(null)} />}
    </aside>
  );
}
