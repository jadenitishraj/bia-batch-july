import { useEffect, useState } from 'react'
import Chat from './Chat.jsx'
import RequestTable from './RequestTable.jsx'
import { streamReply } from './stream.js'

export default function App() {
  const [saved, setSaved] = useState({ requests: [], notices: [], google: 'Connecting' })
  const [chat, setChat] = useState([])
  const [question, setQuestion] = useState('')
  const [busy, setBusy] = useState(false)
  const [live, setLive] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let socket, timer, stopped = false
    function connect() {
      socket = new WebSocket(`ws://${location.host}/ws`)
      socket.onopen = () => setLive(true)
      // Replace the saved snapshot: reconnect does not append duplicate notices.
      socket.onmessage = event => setSaved(JSON.parse(event.data))
      socket.onerror = () => socket.close()
      socket.onclose = () => {
        setLive(false)
        if (!stopped) timer = setTimeout(connect, 1000)
      }
    }
    connect()
    return () => { stopped = true; clearTimeout(timer); socket.close() }
  }, [])

  async function send() {
    const text = question.trim()
    if (!text || busy) return
    const classroom = /request|meeting|email|scheduled/i.test(text)
    const user = { classroom, id: crypto.randomUUID(), role: 'user', text, created: Date.now() / 1000 }
    const answer = { classroom, id: crypto.randomUUID(), role: 'model', text: '', created: user.created + 0.001 }
    setChat(old => [...old, user, answer])
    setQuestion(''); setBusy(true); setError('')
    try {
      const history = chat.filter(message => message.text && !message.classroom).slice(-6).map(({ role, text }) => ({ role, text }))
      await streamReply(text, history, piece => {
        // Update this answer's ID. A WebSocket notice can arrive between pieces.
        setChat(old => old.map(message => message.id === answer.id ? { ...message, text: message.text + piece } : message))
      })
    } catch (problem) { setError(problem.message) }
    finally { setBusy(false) }
  }

  async function sample() {
    await fetch('/api/demo', { method: 'POST' })
  }

  const notices = saved.notices.map(notice => ({ ...notice, role: 'notice' }))
  const messages = [...notices, ...chat].sort((a, b) => a.created - b.created)
  return <div className="app">
    <header><a href="/" className="brand">BIA <span>Student Support Easy</span></a><div className="connection">
      <span className={live ? 'online' : ''}>{live ? '● Live' : '○ Reconnecting'}</span>
      <span>Google: {saved.google}</span>
    </div></header>
    <main>
      <div className="intro"><div><p className="eyebrow">A SMALL CLASSROOM PROJECT</p><h1>Email to meeting. Made easy.</h1>
        <p>New BIA email → free slot → meeting + confirmation → live update.</p></div>
        <button className="secondary" onClick={sample}>Add a sample request</button></div>
      <div className="rule">Automatic for new incoming emails containing <b>BIA</b> in the subject · 30 minutes · 9 am–5 pm India time · no approval step</div>
      {error && <p className="error" role="alert">{error}</p>}
      <div className="workspace">
        <Chat messages={messages} question={question} setQuestion={setQuestion} busy={busy} send={send} />
        <RequestTable requests={saved.requests} />
      </div>
      <footer>Gmail polling · SQLite state · WebSocket updates · HTTP streaming</footer>
    </main>
  </div>
}
