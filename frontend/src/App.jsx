import { useEffect, useMemo, useState } from 'react';
import { decidirConsulta, fetchAudit, fetchDocuments, getDownloadUrl, loginUser, processConsultation } from './api/client';
import AuditPanel from './components/AuditPanel';
import ConfigPanel from './components/ConfigPanel';
import ConsultaPanel from './components/ConsultaPanel';
import DocumentPanel from './components/DocumentPanel';
import LoginCard from './components/LoginCard';
import MainLayout from './components/MainLayout';

const initialResult = {
  sessionId: null,
  status: null,
  triagem: {
    categoria: '—',
    justificativa: 'Aguardando consulta.',
    red_flags: [],
    confianca: 0,
  },
  rag: [],
  sintese: {
    resumo: 'Nenhuma síntese gerada ainda.',
    exames: [],
    medicamentos: [],
  },
  documento: null,
  downloadUrl: '',
};

function buildSintese(data) {
  return {
    resumo: data.sintese?.observacoes || data.sintese?.disclaimer || 'Consulta concluída com sucesso.',
    exames: (data.sintese?.exames_sugeridos || []).map((item) => item.nome || item),
    medicamentos: (data.sintese?.medicacoes_sugeridas || []).map((item) => item.nome || item),
    observacoes: data.sintese?.observacoes || '',
    disclaimer: data.sintese?.disclaimer || '',
  };
}

function App() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [tab, setTab] = useState('consulta');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [login, setLogin] = useState({ username: 'medico', password: 'demo123' });
  const [relato, setRelato] = useState('Paciente de 45 anos relata dor torácica há 3 horas, sudorese, ansiedade e pressão arterial 150/90.');
  const [result, setResult] = useState(initialResult);
  const [auditEvents, setAuditEvents] = useState([]);
  const [documents, setDocuments] = useState([]);

  const canLogin = useMemo(
    () => login.username.trim().length > 0 && login.password.trim().length > 0,
    [login]
  );

  const loadAudit = async () => {
    try {
      const data = await fetchAudit();
      setAuditEvents((data.events || []).map((event) => ({
        time: event.timestamp ? new Date(event.timestamp).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : '--:--',
        actor: event.user_id || event.agent || 'sistema',
        event: event.event_type || 'evento',
        status: event.event_type === 'consulta' ? 'success' : 'ok',
      })));
    } catch (err) {
      setAuditEvents([]);
    }
  };

  const loadDocuments = async () => {
    try {
      const data = await fetchDocuments();
      setDocuments(data.documents || []);
    } catch (err) {
      setDocuments([]);
    }
  };

  useEffect(() => {
    if (tab === 'auditoria') {
      loadAudit();
    }
    if (tab === 'documentos') {
      loadDocuments();
    }
  }, [tab]);

  const handleLogin = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await loginUser(login.username, login.password);
      if (!data.success) {
        throw new Error(data.message || 'Credenciais inválidas');
      }
      setLoggedIn(true);
    } catch (err) {
      setError(err.message || 'Erro ao autenticar');
    } finally {
      setLoading(false);
    }
  };

  const handleProcess = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await processConsultation(relato);

      setResult({
        sessionId: data.session_id,
        status: data.status,
        triagem: data.triagem || initialResult.triagem,
        rag: (data.rag || []).map((item) => item.content || item),
        sintese: buildSintese(data),
        documento: null,
        downloadUrl: '',
      });

      await loadAudit();
      setTab('consulta');
    } catch (err) {
      setError(err.message || 'Erro ao iniciar consulta');
    } finally {
      setLoading(false);
    }
  };

  const handleDecisao = async (decisao, textoEditado) => {
    if (!result.sessionId) {
      return;
    }
    try {
      setLoading(true);
      setError('');
      const data = await decidirConsulta(result.sessionId, decisao, textoEditado);

      const nextDocument = data.documento || null;
      setResult((prev) => ({
        ...prev,
        status: data.status,
        sintese: buildSintese(data),
        documento: nextDocument,
        downloadUrl: nextDocument ? getDownloadUrl(nextDocument) : '',
      }));

      await loadAudit();
      await loadDocuments();
    } catch (err) {
      setError(err.message || 'Erro ao registrar decisão');
    } finally {
      setLoading(false);
    }
  };

  const tabContent = {
    consulta: (
      <ConsultaPanel
        relato={relato}
        setRelato={setRelato}
        loading={loading}
        error={error}
        onProcess={handleProcess}
        onClear={() => setRelato('')}
        onDecidir={handleDecisao}
        result={result}
      />
    ),
    auditoria: <AuditPanel auditEvents={auditEvents} />,
    documentos: <DocumentPanel documents={documents} />,
    config: <ConfigPanel />,
  };

  if (!loggedIn) {
    return (
      <LoginCard
        username={login.username}
        password={login.password}
        onUsernameChange={(e) => setLogin((prev) => ({ ...prev, username: e.target.value }))}
        onPasswordChange={(e) => setLogin((prev) => ({ ...prev, password: e.target.value }))}
        onSubmit={handleLogin}
        loading={loading}
        disabled={!canLogin}
        error={error}
      />
    );
  }

  return (
    <MainLayout tab={tab} setTab={setTab} onLogout={() => setLoggedIn(false)} auditEvents={auditEvents} documents={documents} result={result}>
      {tabContent[tab]}
    </MainLayout>
  );
}

export default App;
