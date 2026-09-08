import { useMemo, useState } from 'react';

const mockMetrics = {
  totalEventos: 128,
  sessoesAtivas: 7,
  latenciaMedia: '2.4s',
  custoEstimado: '$0.23',
};

const auditEvents = [
  { time: '08:20', actor: 'dr.silva', event: 'Triagem iniciada', status: 'ok' },
  { time: '08:22', actor: 'dr.oliveira', event: 'RAG interno consultado', status: 'info' },
  { time: '08:23', actor: 'dr.silva', event: 'Validação humana aprovada', status: 'ok' },
  { time: '08:25', actor: 'sistema', event: 'PDF gerado', status: 'success' },
];

const documents = [
  { name: 'prontuario.pdf', size: '1.2 MB', date: '2026-09-08 08:25' },
  { name: 'atestado.pdf', size: '680 KB', date: '2026-09-08 08:18' },
  { name: 'receita.pdf', size: '540 KB', date: '2026-09-08 08:10' },
];

const systemInfo = [
  ['Modelo', 'BioMistral-medquad-lora'],
  ['Status do RAG', 'Disponível'],
  ['Banco', 'audit.db'],
  ['Documentos', 'data/documents'],
  ['Frontend', 'React + Vite'],
  ['GitHub', 'Flamers-Team/Techchalleng3'],
];

function App() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [tab, setTab] = useState('consulta');
  const [login, setLogin] = useState({ username: 'medico', password: 'demo123' });
  const [relato, setRelato] = useState('Paciente de 45 anos relata desconforto torácico há 3 horas, pressão arterial 150/90, sudorese e ansiedade.');
  const [result, setResult] = useState({
    triagem: {
      categoria: 'Urgência moderada',
      justificativa: 'Sintomas cardíacos compatíveis com avaliação médica urgente.',
      red_flags: ['Dor torácica', 'Sudorese', 'Pressão elevada'],
      confianca: 0.89,
    },
    rag: [
      'Sintomas de dor torácica exigem avaliação imediata com ECG e exames laboratoriais.',
      'Urgência moderada quando há quadro de ansiedade associado a manifestações cardiovasculares.',
    ],
    sintese: {
      resumo: 'Paciente com potencial quadro cardiovascular; suspeita de angina ou arritmia. Avaliação clínica e exames urgentes são indicados.',
      exames: ['ECG', 'Troponina', 'Hemograma completo'],
      medicamentos: ['Não iniciar medicação antes da avaliação médica'],
    },
  });

  const canLogin = useMemo(
    () => login.username === 'medico' && login.password === 'demo123',
    [login]
  );

  const handleLogin = () => {
    if (canLogin) {
      setLoggedIn(true);
    }
  };

  const handleProcess = () => {
    setResult({
      triagem: {
        categoria: 'Urgência moderada',
        justificativa: 'Sintomas de sofrimento cardíaco e risco hemodinâmico em avaliação.',
        red_flags: ['Dor torácica', 'Sudorese', 'Hipertensão'],
        confianca: 0.92,
      },
      rag: [
        'Recomenda-se ECG com interpretação médica imediata.',
        'Considere avaliação de troponina e perfil metabólico.',
        'Acompanhamento clínico obrigatório se houver piora súbita.',
      ],
      sintese: {
        resumo: 'Quadro requer acompanhamento médico atento e exames complementares urgentes.',
        exames: ['ECG', 'Troponina', 'Gasometria', 'Hemograma'],
        medicamentos: ['Ajustar conforme avaliação clínica'],
      },
    });
  };

  const tabContent = {
    consulta: (
      <div className="panel-grid two-cols">
        <div className="panel">
          <h3>Consulta</h3>
          <label>Relato do paciente</label>
          <textarea value={relato} onChange={(e) => setRelato(e.target.value)} rows={12} />
          <div className="button-row">
            <button className="primary" onClick={handleProcess}>Iniciar consulta</button>
            <button className="secondary" onClick={() => setRelato('')}>Limpar</button>
          </div>
        </div>

        <div className="panel">
          <h3>Resultados</h3>
          <div className="result-box">
            <h4>🚨 Triagem</h4>
            <p><strong>Categoria:</strong> {result.triagem.categoria}</p>
            <p><strong>Justificativa:</strong> {result.triagem.justificativa}</p>
            <p><strong>Red flags:</strong> {result.triagem.red_flags.join(', ')}</p>
            <p><strong>Confiança:</strong> {(result.triagem.confianca * 100).toFixed(0)}%</p>
          </div>

          <div className="result-box">
            <h4>📚 RAG</h4>
            <ul>
              {result.rag.map((item, idx) => <li key={idx}>{item}</li>)}
            </ul>
          </div>

          <div className="result-box">
            <h4>🧠 Síntese</h4>
            <p>{result.sintese.resumo}</p>
            <p><strong>Exames:</strong> {result.sintese.exames.join(', ')}</p>
            <p><strong>Medicações:</strong> {result.sintese.medicamentos.join(', ')}</p>
          </div>
        </div>
      </div>
    ),
    auditoria: (
      <div className="panel-grid metrics-grid">
        <div className="panel metric"><span>Total de eventos</span><strong>{mockMetrics.totalEventos}</strong></div>
        <div className="panel metric"><span>Sessões ativas</span><strong>{mockMetrics.sessoesAtivas}</strong></div>
        <div className="panel metric"><span>Latência média</span><strong>{mockMetrics.latenciaMedia}</strong></div>
        <div className="panel metric"><span>Custo estimado</span><strong>{mockMetrics.custoEstimado}</strong></div>

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
              {auditEvents.map((evt, idx) => (
                <tr key={idx}>
                  <td>{evt.time}</td>
                  <td>{evt.actor}</td>
                  <td>{evt.event}</td>
                  <td><span className={`status ${evt.status}`}>{evt.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    ),
    documentos: (
      <div className="panel">
        <h3>Documentos gerados</h3>
        <div className="doc-list">
          {documents.map((doc, idx) => (
            <div key={idx} className="doc-item">
              <div>
                <strong>{doc.name}</strong>
                <small>{doc.date}</small>
              </div>
              <span>{doc.size}</span>
            </div>
          ))}
        </div>
      </div>
    ),
    config: (
      <div className="panel">
        <h3>Configurações do sistema</h3>
        <div className="config-grid">
          {systemInfo.map(([key, value], idx) => (
            <div key={idx} className="config-row">
              <span>{key}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      </div>
    ),
  };

  if (!loggedIn) {
    return (
      <div className="login-shell">
        <div className="login-card">
          <h1>Assistente Médico Inteligente</h1>
          <p>Login do médico</p>

          <label>Usuário</label>
          <input
            value={login.username}
            onChange={(e) => setLogin((prev) => ({ ...prev, username: e.target.value }))}
          />

          <label>Senha</label>
          <input
            type="password"
            value={login.password}
            onChange={(e) => setLogin((prev) => ({ ...prev, password: e.target.value }))}
          />

          <button className="primary full" onClick={handleLogin} disabled={!canLogin}>
            Entrar
          </button>

          {!canLogin && <small className="hint">Use: medico / demo123</small>}
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <strong>Assistente Médico IA</strong>
          <span>Tech Challenge Fase 3</span>
        </div>
        <button className="secondary" onClick={() => setLoggedIn(false)}>Sair</button>
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

      <main className="content">{tabContent[tab]}</main>
    </div>
  );
}

export default App;
