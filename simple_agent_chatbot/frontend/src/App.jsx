// App.jsx
// The whole chat screen.
//
// Left side  = the conversation.
// Right side = what the agent actually did for the last message:
//              user message -> tool call -> tool result -> final answer.

import { useEffect, useRef, useState } from "react";

// Where our FastAPI backend is running
const API = "http://localhost:8001";

// Questions shown as buttons on the empty screen, so a demo can start fast
const SUGGESTIONS = [
  "What is 25 times 4 plus 10?",
  "What is the refund policy?",
  "Remember that I live in Pune",
  "What do you remember about me?",
];

export default function App() {
  // useState creates a variable that React watches.
  // When we change it, the screen is drawn again.
  const [messages, setMessages] = useState([]); // the chat bubbles
  const [steps, setSteps] = useState([]); // the phases of the last run
  const [memory, setMemory] = useState([]); // long term memory facts
  const [history, setHistory] = useState([]); // the whole short term memory
  const [memorySize, setMemorySize] = useState(0); // how many old messages were sent
  const [input, setInput] = useState(""); // what the user is typing
  const [loading, setLoading] = useState(false);

  // This lets us scroll to the bottom when a new message arrives
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // This runs when the user clicks Send, or clicks a suggestion
  async function sendMessage(textFromButton) {
    const question = textFromButton || input;
    if (question.trim() === "" || loading) return;

    setInput("");
    setMessages((old) => [...old, { role: "user", text: question }]);
    setLoading(true);

    // Call the FastAPI backend
    const response = await fetch(API + "/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: question, session_id: "default" }),
    });

    const data = await response.json();

    // Put the answer on the screen
    setMessages((old) => [...old, { role: "bot", text: data.answer }]);
    setSteps(data.steps);
    setMemory(data.long_term_memory);
    setHistory(data.short_term_memory);
    // minus 2, because this question and its answer were just added to memory
    setMemorySize(data.short_term_memory_size - 2);
    setLoading(false);
  }

  return (
    <div className="app">
      {/* ================= LEFT: the conversation ================= */}
      <main className="chat-panel">
        <header className="topbar">
          <div className="avatar">B</div>
          <div>
            <div className="topbar-name">Bia</div>
            <div className="topbar-sub">LangChain agent · 15 tools</div>
          </div>
        </header>

        <div className="thread">
          {/* Nothing said yet: show a greeting and some starter questions */}
          {messages.length === 0 && (
            <div className="welcome">
              <h1>How can I help?</h1>
              <p>
                I can do maths, look things up in the company documents, and
                remember things about you.
              </p>
              <div className="suggestions">
                {SUGGESTIONS.map((text) => (
                  <button key={text} onClick={() => sendMessage(text)}>
                    {text}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={"row " + m.role}>
              {m.role === "bot" && <div className="avatar small">B</div>}
              <div className="bubble">{m.text}</div>
            </div>
          ))}

          {loading && (
            <div className="row bot">
              <div className="avatar small">B</div>
              <div className="typing">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div className="composer">
          <input
            value={input}
            placeholder="Ask anything..."
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />
          <button
            className="send"
            onClick={() => sendMessage()}
            disabled={input.trim() === "" || loading}
          >
            ↑
          </button>
        </div>
      </main>

      {/* ================= RIGHT: what the agent did ================= */}
      <aside className="side-panel">
        <section className="side-block">
          <h2>Long term memory</h2>
          <div className="side-note">Saved in data/long_term_memory.json</div>
          <div className="chips">
            {memory.length === 0 && <span className="chip empty">empty</span>}
            {memory.map((fact, i) => (
              <span key={i} className="chip">
                {fact}
              </span>
            ))}
          </div>
        </section>

        <section className="side-block">
          <h2>Short term memory</h2>
          <div className="side-note">
            The whole conversation we keep in RAM. This is re-sent to the model
            with every question. Lost when the server restarts.
          </div>
          {/* JSON.stringify(value, null, 2) prints the JSON nicely indented */}
          <pre className="json">
            {history.length === 0 ? "[]" : JSON.stringify(history, null, 2)}
          </pre>
        </section>

        <section className="side-block grow">
          <h2>What the agent did</h2>

          {steps.length === 0 && (
            <div className="side-note">Send a message to see the phases.</div>
          )}

          {memorySize > 0 && (
            <div className="memory-note">
              Short term memory: {memorySize} older messages were also sent to
              the model with this question.
            </div>
          )}

          {steps.map((step, i) => (
            <div key={i} className={"step " + step.phase.replace(" ", "-")}>
              <div className="step-head">
                <span className="step-num">{i + 1}</span>
                <span className="step-phase">{step.phase}</span>
              </div>
              <div className="step-title">{step.title}</div>
              <pre>{step.detail}</pre>
            </div>
          ))}
        </section>
      </aside>
    </div>
  );
}
