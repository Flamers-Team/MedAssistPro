export default function AuditPanel({ auditEvents }) {
  return (
    <div className="panel-grid metrics-grid">
      <div className="panel metric"><span>Total de eventos</span><strong>{auditEvents.length}</strong></div>
      <div className="panel metric"><span>Sessões ativas</span><strong>{new Set(auditEvents.map((e) => e.actor)).size}</strong></div>
      <div className="panel metric"><span>Último evento</span><strong>{auditEvents[0]?.time || '--:--'}</strong></div>
      <div className="panel metric"><span>Status</span><strong>{auditEvents.length ? 'ativo' : 'sem logs'}</strong></div>

      <div className="panel full-width">
        <h3>Eventos recentes</h3>
        <table>
          <thead>
            <tr>
              <th>Hora</th>
              <th>Agente</th>
              <th>Evento</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {auditEvents.length > 0 ? auditEvents.map((evt, idx) => (
              <tr key={idx}>
                <td>{evt.time}</td>
                <td>{evt.actor}</td>
                <td>{evt.event}</td>
                <td><span className={`status ${evt.status}`}>{evt.status}</span></td>
              </tr>
            )) : (
              <tr><td colSpan="4">Nenhum evento registrado ainda.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
