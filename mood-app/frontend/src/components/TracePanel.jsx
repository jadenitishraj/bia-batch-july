// The popup behind the 👁 button. It shows one answer's whole story:
// what we sent to the LLM, every tool it asked for, and the raw JSON of all of it.

import { useEffect, useState } from "react";

import { api } from "../api";
import { Modal } from "./ui";
import Part from "./TracePart";

// Turn any value into neat, indented JSON
const pretty = (value) => JSON.stringify(value, null, 2);

export default function TracePanel({ trace, onClose }) {
  const [explanation, setExplanation] = useState("");

  // Ask the backend to describe this trace in plain words, once, when the popup opens
  useEffect(() => {
    api
      .explain(trace)
      .then((data) => setExplanation(data.explanation))
      .catch(() => setExplanation("Could not load the explanation. Is the backend running?"));
  }, [trace]);

  const { sent_to_llm: sent, steps, usage } = trace;

  return (
    <Modal title="What happened behind this answer" onClose={onClose} wide>
      <Part
        number="1"
        title="What we sent to the LLM"
        note={`Every question sends all of this again: the instructions, the
               ${sent.conversation_so_far.length} earlier messages, the new question, and the names
               of ${sent.tools_offered.length} tools the LLM is allowed to ask for.`}
      >
        <p className="meta">
          model <code>{sent.model}</code>
        </p>

        <p className="sub">The instructions it always gets</p>
        <pre className="prose">{sent.system_instructions}</pre>

        <p className="sub">The {sent.tools_offered.length} tools it may ask for</p>
        <div className="tool-list">
          {sent.tools_offered.map((name) => (
            <code className="step-tool" key={name}>
              {name}
            </code>
          ))}
        </div>

        <p className="sub">The conversation and the new question</p>
        <pre className="json">
          {pretty({
            conversation_so_far: sent.conversation_so_far,
            new_user_message: sent.new_user_message,
          })}
        </pre>
      </Part>

      <Part
        number="2"
        title="What happened, step by step"
        note="Notice the LLM never touches the database. It only asks for a tool by name, our
              Python code runs it, and we send the answer back."
      >
        {steps.map((step, index) => (
          <div className="step" key={index}>
            <div className="step-head">
              <span className={step.who === "LLM" ? "who who-llm" : "who who-code"}>{step.who}</span>
              <span className="step-what">{step.what}</span>
              {step.tool && <code className="step-tool">{step.tool}()</code>}
            </div>
            {step.arguments && <pre className="json">{pretty(step.arguments)}</pre>}
            {step.result !== undefined && <pre className="json">{pretty(step.result)}</pre>}
            {step.text && <p className="step-text">{step.text}</p>}
          </div>
        ))}
      </Part>

      <Part
        number="3"
        title="The conversation the LLM now has"
        note="This whole list is sent again with your next question. That is how the agent
              remembers the past conversation and the tool results."
      >
        <details>
          <summary>Show the full JSON</summary>
          <pre className="json">{pretty(trace.conversation_after_the_run)}</pre>
        </details>
        <p className="meta">
          {usage.calls_to_the_llm} calls to the LLM · {usage.input_tokens} tokens in ·{" "}
          {usage.output_tokens} tokens out
        </p>
      </Part>

      <Part number="4" title="The same thing, explained in simple words">
        {explanation ? (
          <p className="explain">{explanation}</p>
        ) : (
          <p className="explain muted">Asking the LLM to explain this…</p>
        )}
      </Part>
    </Modal>
  );
}
