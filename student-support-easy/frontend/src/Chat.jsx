import { useEffect, useRef } from 'react'

export default function Chat({ messages, question, setQuestion, busy, send }) {
  const bottom = useRef(null)
  useEffect(() => {
    bottom.current?.scrollIntoView({ block: 'nearest' })
  }, [messages])
  return <section className="panel chat-panel">
    <div className="panel-heading">
      <h2>Classroom chat</h2>
      <p>Gemini streams answers. Gmail updates appear automatically.</p>
    </div>
    <div className="messages" role="log" aria-live="polite">
      {messages.length === 0 && <div className="welcome">
        <span>✦</span><h3>Small code. A complete story.</h3>
        <p>Ask about your requests, or anything you are learning.</p>
      </div>}
      {messages.map(message => <article key={message.id} className={'message ' + message.role}>
        <b>{message.role === 'user' ? 'You' : message.role === 'notice' ? 'Live classroom update' : 'Easy AI'}</b>
        <p>{message.text || 'Thinking…'}</p>
      </article>)}
      <div ref={bottom} />
    </div>
    <form className="composer" onSubmit={event => { event.preventDefault(); send() }}>
      <textarea aria-label="Message Easy AI" placeholder="What requests have I received so far?" value={question}
        onChange={event => setQuestion(event.target.value)} rows={2}
        onKeyDown={event => {
          if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); send() }
        }} />
      <div><small>{busy ? 'Gemini is streaming… live updates still work.' : 'SQLite facts · real Gemini answers'}</small>
        <button disabled={busy || !question.trim()}>{busy ? 'Replying…' : 'Send'}</button></div>
    </form>
  </section>
}
