export default function MainLayout({
  tab,
  setTab,
  onLogout,
  auditEvents,
  documents,
  result,
  children,
}) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <strong>Assistente Médico IA</strong>
          <span>Tech Challenge Fase 3</span>
        </div>
        <button className="secondary" onClick={onLogout}>Sair</button>
      </header>

      <nav className="tabs">
        {['consulta', 'auditoria', 'documentos', 'config'].map((item) => (
          <button
            key={item}
            className={tab === item ? 'tab active' : 'tab'}
            onClick={() => setTab(item)}
          >
            {item === 'consulta' && 'Consulta'}
            {item === 'auditoria' && 'Auditoria'}
            {item === 'documentos' && 'Documentos'}
            {item === 'config' && 'Config'}
          </button>
        ))}
      </nav>

      <main className="content">{children}</main>
    </div>
  );
}
