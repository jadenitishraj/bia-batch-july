import React, { useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { ArrowUp, BookOpen, CalendarDays, Check, Mail, Play, Radio, Settings2, ShieldCheck, Sparkles, Wifi, WifiOff, X } from 'lucide-react'
import './style.css'
import LocalReport from './LocalReport.jsx'
const time = value => value ? new Date(value).toLocaleString([], { timeZone: 'Asia/Kolkata', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Not polled yet'
function combine(current, incoming) {
  const indexed = new Map(current.map(m => [m.id, m]))
  for (const m of incoming) { const old = indexed.get(m.id); if (!old || m.revision >= old.revision) indexed.set(m.id, m) }
  return [...indexed.values()].sort((a, b) => a.seq - b.seq)
}

function App() {
  const [messages, setMessages] = useState([]), [snapshot, setSnapshot] = useState(null), [connection, setConnection] = useState('Connecting')
  const [input, setInput] = useState(''), [busy, setBusy] = useState(false), [demoBusy, setDemoBusy] = useState(false), [settings, setSettings] = useState(false)
  const [error, setError] = useState(''), [notice, setNotice] = useState(''), [chunks, setChunks] = useState({})
  const feed = useRef(null), follow = useRef(true), controller = useRef(null), cursor = useRef(-1)
  const merge = items => setMessages(current => combine(current, items))
  useEffect(() => {
    let stopped = false, socket, timer, attempt = 0
    function accept(data) {
      if (stopped) return
      merge(data.chat || [])
      if (data.cursor >= cursor.current) { cursor.current = data.cursor; setSnapshot(data) }
    }
    fetch('/api/snapshot').then(r => { if (!r.ok) throw Error(); return r.json() }).then(accept).catch(() => { if (!stopped) setError('Cannot load the conversation. Check that FastAPI is running.') })
    function connect() {
      setConnection('Connecting')
      socket = new WebSocket(`${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/ws`)
      socket.onopen = () => { attempt = 0; setConnection('Live') }
      socket.onmessage = event => { try { accept(JSON.parse(event.data)) } catch { setError('An update could not be read. Reconnect to reload the saved conversation.') } }
      socket.onerror = () => socket.close()
      socket.onclose = () => { if (!stopped) { setConnection('Reconnecting'); timer = setTimeout(connect, Math.min(1000 * 2 ** attempt++, 10000)) } }
    }
    connect()
    return () => { stopped = true; clearTimeout(timer); socket?.close(); controller.current?.abort() }
  }, [])
  useEffect(() => { if (follow.current && feed.current) feed.current.scrollTop = feed.current.scrollHeight }, [messages, busy])
  async function post(path, payload) {
    setError(''); const r = await fetch(path, { method: 'POST', ...(payload === undefined ? {} : { headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) }) }), body = await r.json()
    if (!r.ok) throw Error(typeof body.detail === 'string' ? body.detail : 'The action could not be completed.')
    return body
  }
  async function demo() {
    setDemoBusy(true); follow.current = true
    try { setNotice(`${(await post('/api/demo')).ref}: the email and tutoring changes will arrive in this conversation.`) }
    catch (e) { setError(e.message) } finally { setTimeout(() => setDemoBusy(false), 5000) }
  }
  async function proposalDemo() { try { setNotice((await post('/api/automation/demo')).message); follow.current=true } catch(e) { setError(e.message) } }
  async function setupAutomation() { try { setNotice((await post('/api/automation/authorize')).message) } catch(e) { setError(e.message) } }
  async function monitor() { try { setNotice((await post('/api/automation/activation', {enabled: !snapshot?.automation.enabled})).message) } catch(e) { setError(e.message) } }
  async function approve(ref, revision) { try { setNotice((await post(`/api/proposals/${ref}/approve`, {revision})).message) } catch(e) { setError(e.message) } }
  async function google() { try { setNotice((await post('/api/google/connect')).message) } catch (e) { setError(e.message) } }
  async function ask(text = input) {
    const question = text.trim(); if (!question || busy) return
    setBusy(true); setInput(''); setError(''); follow.current = true
    // Send saved IDs of the nearby messages the user can actually see, never their text.
    const bounds = feed.current?.getBoundingClientRect()
    const visibleIds = bounds ? [...feed.current.querySelectorAll('[data-message-id]')].filter(node => {
      const rect = node.getBoundingClientRect()
      return rect.bottom > bounds.top && rect.top < bounds.bottom
    }).slice(-10).map(node => node.dataset.messageId) : undefined
    const id = crypto.randomUUID(), temporary = { id: `user:${id}`, role: 'user', content: question, state: 'complete', revision: 0, seq: (messages.at(-1)?.seq || 0) + 1, at: new Date().toISOString(), metadata: {} }
    merge([temporary]); controller.current = new AbortController()
    try {
      const response = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: question, request_id: id, context_message_ids: visibleIds }), signal: controller.current.signal })
      if (!response.ok) { const body = await response.json(); throw Error(typeof body.detail === 'string' ? body.detail : 'The question could not be sent.') }
      const reader = response.body.getReader(), decoder = new TextDecoder(); let buffer = '', terminal = false
      while (true) {
        const { done, value } = await reader.read(); buffer += decoder.decode(value, { stream: !done }); let boundary
        while ((boundary = buffer.indexOf('\n\n')) !== -1) {
          const packet = buffer.slice(0, boundary); buffer = buffer.slice(boundary + 2)
          const line = packet.split('\n').find(x => x.startsWith('data: '))
          if (line) {
            const item = JSON.parse(line.slice(6)); merge([item.message])
            if (item.type === 'delta') setChunks(c => ({ ...c, [item.message.id]: (c[item.message.id] || 0) + 1 }))
            if (item.message.state !== 'streaming') terminal = true
          }
        }
        if (done) break
      }
      if (!terminal) setError('The reply connection ended. Saved text will recover through live updates; reload if needed.')
    } catch (e) {
      if (e.name !== 'AbortError') setError(e.message || 'Connection lost. Saved replies return when the conversation reconnects.')
      setMessages(c => c.filter(m => m.id !== temporary.id || m.revision > 0))
    } finally { setBusy(false); controller.current = null }
  }
  const g = snapshot?.google, suggestions = ['Who is still waiting for a session?', 'When is the FastAPI tutoring session?', 'Explain WebSockets in simple terms']
  return <div className="app">
    <header className="header"><a className="brand" href="/"><span className="brand-icon"><BookOpen size={21}/></span><span>BIA <span className="brand-divider">/</span> <b>Classroom AI</b><small>July Batch · Student support</small></span></a><div className="header-actions"><span className={`live ${connection === 'Live' ? 'online' : ''}`}>{connection === 'Live' ? <Wifi size={14}/> : <WifiOff size={14}/>} {connection}</span><button className="quiet-button" onClick={demo} disabled={demoBusy || !snapshot}><Play size={14}/>{demoBusy ? 'Demo running…' : 'Run demo'}</button><button className={`settings-button ${settings ? 'active' : ''}`} aria-label="Connection settings" aria-expanded={settings} onClick={() => setSettings(!settings)}><Settings2 size={19}/></button></div></header>
    {settings && <section className="settings" aria-label="Connections"><div><h2><Sparkles size={16}/> Gemini</h2><p>{snapshot?.gemini.configured ? snapshot.gemini.model : 'API key needed on the server'}</p><small>Your questions and only relevant classroom records are sent to Gemini.</small></div><div><h2><ShieldCheck size={16}/> Google · {g?.state === 'connected' ? 'Connected' : g?.state === 'authorizing' ? 'Awaiting consent' : 'Needs attention'}</h2><p>Gmail & Calendar · read-only</p><small>Last successful poll: {time(g?.last_poll)}</small><button onClick={google} disabled={!g?.client_configured || g?.state === 'authorizing'}>{g?.state === 'connected' ? 'Reconnect Google' : 'Connect Google'}</button></div><div className="automation-settings"><h2>Approval-first scheduling</h2><p>{snapshot?.automation.enabled ? 'Monitoring new requests for proposals' : 'Proposal monitoring is off'}</p><small>New labeled emails can produce a 30-minute proposal between 9 am and 5 pm India time. Every meeting, sender invitation and email confirmation requires your approval of its specific time. Existing requests are not backfilled.</small><div className="automation-controls"><button onClick={proposalDemo}>Run safe proposal simulation</button><button onClick={setupAutomation} disabled={snapshot?.automation.authorizing}>{snapshot?.automation.authorizing ? 'Waiting for Google consent…' : 'Authorize scheduling & email permissions'}</button><button onClick={monitor} disabled={!snapshot?.automation.authorized}>{snapshot?.automation.enabled ? 'Pause proposal monitoring' : 'Enable new-request proposals'}</button></div></div><p className="setup-note">Apply Gmail label <code>BIA-Support</code> to a synthetic email with <code>[SUP-CLASS001]</code> in its subject. Use the same reference in a one-off Calendar event title. A new meeting and threaded confirmation are sent only after you approve its specific proposal. Full setup is in the README.</p></section>}
    <main className="chat-layout"><div className="conversation" ref={feed} onScroll={() => { if (feed.current) follow.current = feed.current.scrollHeight - feed.current.scrollTop - feed.current.clientHeight < 120 }} aria-label="Classroom conversation"><div className="conversation-inner"><section className="intro"><span className="intro-label"><Sparkles size={14}/> YOUR CLASSROOM ASSISTANT</span><h1>Your classroom,<br/><span>in conversation.</span></h1><p>Ask a question. Follow a support request. See tutoring changes the moment they arrive.</p><div className="intro-note"><Radio size={14}/> Classroom updates appear here automatically.</div></section><div className="day-divider"><span>Saved conversation</span></div>
      <div className="messages" role="log" aria-live="polite" aria-relevant="additions text">{messages.map(m => {
        const meta = m.metadata || {}, streaming = m.state === 'streaming'
        if (m.role === 'notification') return <article className="notification" key={m.id} data-message-id={m.id}><span className={`event-icon ${meta.source}`}>{meta.source === 'calendar' ? <CalendarDays size={17}/> : meta.source === 'gmail' ? <Mail size={17}/> : <Check size={17}/>}</span><div><div className="message-label"><b>{meta.source === 'calendar' ? 'Calendar update' : meta.source === 'gmail' ? 'Support email' : 'Support update'}</b>{meta.origin && meta.origin !== 'google' && <span className="sample-label">{meta.origin === 'demo' ? 'Classroom demo' : 'Sample'}</span>}<time>{time(m.at)}</time></div><div className="message-text">{m.content}</div>{meta.proposal_start && meta.workflow_stage === 'awaiting_approval' && <div className="session-time">Proposal: {time(meta.proposal_start)} · 30 minutes · India time</div>}{meta.workflow_stage === 'awaiting_approval' && snapshot?.jobs?.some(j => j.ref === meta.ref && j.stage === 'awaiting_approval' && j.revision === meta.proposal_revision) && <button className="approve-button" onClick={() => approve(meta.ref, meta.proposal_revision)}>Approve meeting, sender invitation & confirmation</button>}{meta.session_at && <div className="session-time"><CalendarDays size={13}/> Tutoring: {time(meta.session_at)}</div>}</div></article>
        return <article className={`chat-message ${m.role}`} key={m.id} data-message-id={m.id} data-state={m.state} data-chunks={chunks[m.id] || 0}>{m.role === 'assistant' && <span className="assistant-icon"><Sparkles size={17}/></span>}<div className="bubble-wrap"><div className="message-label"><b>{m.role === 'user' ? 'You' : 'Classroom AI'}</b><time>{time(m.at)}</time></div><div className="bubble"><div className="message-text">{m.content || (streaming ? 'Thinking…' : 'No reply text was returned.')}{streaming && m.content && <span className="typing-cursor" aria-label="Reply streaming"/>}</div>{meta.local_report && <LocalReport report={meta.local_report}/>} {meta.error && <p className="reply-error" role="alert">{meta.error}</p>}{m.state === 'interrupted' && !meta.error && <p className="reply-error">Reply interrupted. Send the question again to continue.</p>}</div>{m.role === 'assistant' && <div className="reply-details"><span>{meta.grounding_kind === 'classroom' ? `Saved classroom snapshot · ${meta.matched ?? 0} matches${meta.origins?.some(o => o !== 'google') ? ' · includes demo/sample data' : ''}` : meta.local_action ? 'Local workflow action' : 'Gemini response'}</span>{streaming ? <span className="stream-state">Streaming{chunks[m.id] ? ` · ${chunks[m.id]} chunks` : '…'}</span> : chunks[m.id] ? <span>{chunks[m.id]} streamed chunks</span> : null}</div>}</div></article>
      })}</div></div></div>
      <div className="compose-area"><div className="compose-inner">{(error || notice) && <div className={`banner ${error ? 'error' : ''}`} role={error ? 'alert' : 'status'}><span>{error || notice}</span><button aria-label="Dismiss message" onClick={() => { setError(''); setNotice('') }}><X size={14}/></button></div>}<div className="suggestions">{suggestions.map(text => <button key={text} onClick={() => ask(text)} disabled={busy}>{text}</button>)}</div><form className="composer" onSubmit={e => { e.preventDefault(); ask() }}><textarea aria-label="Message Classroom AI" placeholder="Ask about your classroom, or anything you're learning…" value={input} onChange={e => setInput(e.target.value)} maxLength={4000} rows={2} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); ask() } }}/><div className="composer-bottom"><span><Sparkles size={13}/>{busy ? 'Gemini is replying. Live updates can still arrive.' : 'Gemini · grounded in your tracked classroom'}</span><button className="send" type="submit" disabled={busy || !input.trim()} aria-label="Send message"><ArrowUp size={19}/></button></div></form><div className="footnote"><span><ShieldCheck size={12}/> Approval-first Google access</span><span>AI can make mistakes. Classroom answers use the last saved poll.</span><span className="google-status">{g?.state === 'connected' ? 'Google connected' : g?.state === 'authorizing' ? 'Google consent pending' : 'Google setup needed'}</span></div></div></div>
    </main>
  </div>
}
createRoot(document.getElementById('root')).render(<App/> )
