import React, {useState, useEffect} from 'react'
const time = value => value ? new Date(value).toLocaleString([], { timeZone:'Asia/Kolkata', month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' }) : 'Not recorded'
export default function LocalReport({ report }) {
  const [rows, setRows] = useState(report.rows || [])
  const [guests, setGuests] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => {
    if (report.type !== 'guests') return
    let active = true
    fetch(`/api/requests/${report.ref}/guests`).then(async r => { const data = await r.json(); if (!r.ok) throw Error(data.detail); return data }).then(data => { if (active) setGuests(data) }).catch(e => { if (active) setError(e.message) })
    return () => { active = false }
  }, [report.type, report.ref])
  async function more() {
    setLoading(true)
    try {
      const response = await fetch(`/api/reports/${report.report_id}?offset=${rows.length}`), data = await response.json()
      if (!response.ok) throw Error(data.detail || 'Could not load saved rows.')
      setRows(current => [...current, ...data.rows])
    } catch (e) { setError(e.message) } finally { setLoading(false) }
  }
  if (report.type === 'guests') return <section className="local-report"><b>Guests · {report.ref}</b>{error ? <p role="alert">{error}</p> : !guests ? <p>Reading only this tracked meeting's guest details…</p> : <><p>{guests.message || `${guests.guests.length} guest(s)${guests.partial ? ' · partial response' : ''}`}</p><ul>{guests.guests.map(guest => <li key={guest.email}>{guest.displayName || guest.email}{guest.displayName ? ` (${guest.email})` : ''} · {guest.responseStatus || 'Response unknown'}</li>)}</ul></>}<small>Guest identities are rendered locally on your explicit request; they are not sent to Gemini.</small></section>
  return <section className="local-report"><div className="report-heading"><b>Tracked requests · {report.total} total</b><span>{rows.length} shown</span></div>{report.scope?.window_seconds && <p>Received within the last {report.scope.window_seconds / 60} minutes, as of {time(report.scope.captured_at)}.</p>}{report.scope?.fallback_rows > 0 && <p>{report.scope.fallback_rows} row(s) use first observation because original receive time is not known.</p>}<div className="table-scroll"><table><thead><tr><th>Reference</th><th>Subject</th><th>Received</th><th>Workflow / status</th><th>Meeting / proposal</th></tr></thead><tbody>{rows.map(row => <tr key={row.ref}><td>{row.ref}<small>{row.origin}</small></td><td>{row.title}</td><td>{time(row.received_at)}<small>{row.received_basis === 'gmail_internal_date' ? 'Original Gmail time' : 'First-observed fallback'}</small></td><td>{row.workflow_stage.replaceAll('_',' ')}<small>{row.status.replaceAll('_',' ')}</small>{row.error && <small>{row.error}</small>}</td><td>{time(row.session_at || row.proposal_at)}{!row.session_at && row.proposal_at && <small>{row.workflow_stage === 'awaiting_approval' ? 'Proposal only' : 'Recorded time; not currently scheduled'}</small>}</td></tr>)}</tbody></table></div>{rows.length < report.total && <button onClick={more} disabled={loading}>{loading ? 'Loading…' : 'Load 20 more saved rows'}</button>}{error && <p role="alert">{error}</p>}</section>
}
