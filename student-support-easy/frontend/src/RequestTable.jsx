export default function RequestTable({ requests }) {
  return <section className="panel request-panel">
    <div className="panel-heading">
      <h2>Saved requests <span>{requests.length}</span></h2>
      <p>Every row comes from SQLite. Updates arrive live.</p>
    </div>
    <div className="table-scroll">
      <table>
        <thead><tr><th>Email subject</th><th>Status</th><th>Meeting · India time</th></tr></thead>
        <tbody>
          {requests.map(request => <tr key={request.id}>
            <td>{request.subject}{request.error && <small>{request.error}</small>}</td>
            <td><span className={'badge ' + (request.status.startsWith('done') ? 'done' : '')}>{request.status}</span></td>
            <td>{request.meeting_time || 'Not scheduled yet'}</td>
          </tr>)}
        </tbody>
      </table>
      {requests.length === 0 && <div className="empty">
        <strong>Ready for the first BIA email</strong>
        <p>A new incoming email with BIA in its subject will appear here.</p>
      </div>}
    </div>
  </section>
}
