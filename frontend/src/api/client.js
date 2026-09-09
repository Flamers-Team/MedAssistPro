const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

async function requestJson(url, options = {}) {
  const response = await fetch(`${API_URL}${url}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || data.message || 'Erro na requisição');
  }

  return data;
}

export const loginUser = (username, password) =>
  requestJson('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });

export const processConsultation = (relato) =>
  requestJson('/api/consulta', {
    method: 'POST',
    body: JSON.stringify({
      relato,
      paciente: { nome: 'Maria Silva', idade: 45, sexo: 'F' },
      medico: { nome: 'Dr. João', crm: '12345-SP' },
    }),
  });

export const fetchAudit = () => requestJson('/api/auditoria');
export const fetchDocuments = () => requestJson('/api/documentos');
export const getDownloadUrl = (path) => `${API_URL}/api/download?path=${encodeURIComponent(path)}`;

export { API_URL };
