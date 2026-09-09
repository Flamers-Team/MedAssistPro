import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  API_URL,
  fetchAudit,
  fetchDocuments,
  getDownloadUrl,
  loginUser,
  processConsultation,
} from './client';

function mockFetchOnce(body, { ok = true, status = 200 } = {}) {
  global.fetch = vi.fn().mockResolvedValue({
    ok,
    status,
    json: () => Promise.resolve(body),
  });
}

describe('api/client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('loginUser envia usuario e senha para /api/auth/login', async () => {
    mockFetchOnce({ success: true, message: 'Login validado', username: 'medico' });

    const result = await loginUser('medico', 'demo123');

    expect(global.fetch).toHaveBeenCalledWith(
      `${API_URL}/api/auth/login`,
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ username: 'medico', password: 'demo123' }),
      })
    );
    expect(result.success).toBe(true);
  });

  it('processConsultation envia o relato e dados default de paciente/medico', async () => {
    mockFetchOnce({ session_id: 'abc', status: 'ok' });

    await processConsultation('Paciente relata febre.');

    const [, options] = global.fetch.mock.calls[0];
    const sentBody = JSON.parse(options.body);
    expect(sentBody.relato).toBe('Paciente relata febre.');
    expect(sentBody.paciente).toBeTruthy();
    expect(sentBody.medico).toBeTruthy();
  });

  it('fetchAudit chama /api/auditoria', async () => {
    mockFetchOnce({ events: [], total: 0 });
    await fetchAudit();
    expect(global.fetch).toHaveBeenCalledWith(`${API_URL}/api/auditoria`, expect.any(Object));
  });

  it('fetchDocuments chama /api/documentos', async () => {
    mockFetchOnce({ documents: [] });
    await fetchDocuments();
    expect(global.fetch).toHaveBeenCalledWith(`${API_URL}/api/documentos`, expect.any(Object));
  });

  it('getDownloadUrl monta a URL com o path codificado', () => {
    const url = getDownloadUrl('C:\\docs\\prontuario 1.pdf');
    expect(url).toBe(`${API_URL}/api/download?path=${encodeURIComponent('C:\\docs\\prontuario 1.pdf')}`);
  });

  it('lanca erro com a mensagem do backend quando a resposta nao e ok', async () => {
    mockFetchOnce({ detail: 'Relato do paciente não pode estar vazio.' }, { ok: false, status: 400 });

    await expect(processConsultation('')).rejects.toThrow('Relato do paciente não pode estar vazio.');
  });

  it('lanca erro generico quando a resposta falha sem corpo JSON valido', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.reject(new Error('invalid json')),
    });

    await expect(fetchAudit()).rejects.toThrow('Erro na requisição');
  });
});
