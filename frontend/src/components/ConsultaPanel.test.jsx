import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ConsultaPanel from './ConsultaPanel';

const baseResult = {
  sessionId: null,
  status: null,
  triagem: {
    categoria: 'URGENTE',
    justificativa: 'Dor toracica ha 3 horas.',
    red_flags: ['dor toracica'],
    confianca: 'alta',
  },
  rag: [],
  sintese: {
    resumo: 'Possivel sindrome coronariana aguda.',
    exames: ['ECG', 'Troponina'],
    medicamentos: [],
  },
  documento: null,
  downloadUrl: '',
};

function renderPanel(overrides = {}) {
  const props = {
    relato: 'Paciente relata dor toracica.',
    setRelato: vi.fn(),
    loading: false,
    error: '',
    onProcess: vi.fn(),
    onClear: vi.fn(),
    onDecidir: vi.fn(),
    result: baseResult,
    ...overrides,
  };
  render(<ConsultaPanel {...props} />);
  return props;
}

describe('ConsultaPanel', () => {
  it('mostra a categoria de triagem e os red flags', () => {
    renderPanel();
    expect(screen.getByText('URGENTE')).toBeInTheDocument();
    expect(screen.getByText('dor toracica')).toBeInTheDocument();
  });

  it('mostra "Nenhum" quando nao ha red flags', () => {
    renderPanel({
      result: { ...baseResult, triagem: { ...baseResult.triagem, red_flags: [] } },
    });
    expect(screen.getByText('Nenhum')).toBeInTheDocument();
  });

  it('chama onProcess ao clicar em Iniciar consulta', async () => {
    const user = userEvent.setup();
    const props = renderPanel();

    await user.click(screen.getByRole('button', { name: 'Iniciar consulta' }));

    expect(props.onProcess).toHaveBeenCalledTimes(1);
  });

  it('desabilita o botao e mostra "Processando..." durante loading', () => {
    renderPanel({ loading: true });
    expect(screen.getByRole('button', { name: 'Processando...' })).toBeDisabled();
  });

  it('exibe mensagem de erro quando presente', () => {
    renderPanel({ error: 'Erro ao iniciar consulta' });
    expect(screen.getByText('Erro ao iniciar consulta')).toBeInTheDocument();
  });

  it('nao exibe link de download nem botoes de decisao quando nenhuma consulta rodou', () => {
    renderPanel();
    expect(screen.queryByRole('link', { name: 'Baixar PDF' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Aprovar' })).not.toBeInTheDocument();
  });

  describe('quando aguardando validação médica', () => {
    const aguardando = { ...baseResult, sessionId: 'sess-1', status: 'aguardando_validacao' };

    it('mostra os botões de aprovar/editar/rejeitar e nenhum link de download', () => {
      renderPanel({ result: aguardando });
      expect(screen.getByRole('button', { name: 'Aprovar' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Editar e aprovar' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Rejeitar' })).toBeInTheDocument();
      expect(screen.queryByRole('link', { name: 'Baixar PDF' })).not.toBeInTheDocument();
    });

    it('chama onDecidir("aprovado") ao clicar em Aprovar', async () => {
      const user = userEvent.setup();
      const props = renderPanel({ result: aguardando });

      await user.click(screen.getByRole('button', { name: 'Aprovar' }));

      expect(props.onDecidir).toHaveBeenCalledWith('aprovado');
    });

    it('chama onDecidir("rejeitado") ao clicar em Rejeitar', async () => {
      const user = userEvent.setup();
      const props = renderPanel({ result: aguardando });

      await user.click(screen.getByRole('button', { name: 'Rejeitar' }));

      expect(props.onDecidir).toHaveBeenCalledWith('rejeitado');
    });

    it('abre o editor de texto e chama onDecidir("editado", texto) ao confirmar', async () => {
      const user = userEvent.setup();
      const props = renderPanel({ result: aguardando });

      await user.click(screen.getByRole('button', { name: 'Editar e aprovar' }));
      const textarea = screen.getByLabelText('Texto editado (substitui a queixa principal no documento)');
      await user.clear(textarea);
      await user.type(textarea, 'Texto revisado');
      await user.click(screen.getByRole('button', { name: 'Confirmar edição e aprovar' }));

      expect(props.onDecidir).toHaveBeenCalledWith('editado', 'Texto revisado');
    });
  });

  it('exibe o link de download quando aprovado com documento gerado', () => {
    renderPanel({
      result: { ...baseResult, status: 'ok', documento: 'prontuario_123.pdf', downloadUrl: 'http://x/api/download?path=abc' },
    });
    expect(screen.getByRole('link', { name: 'Baixar PDF' })).toHaveAttribute(
      'href',
      'http://x/api/download?path=abc'
    );
    expect(screen.queryByRole('button', { name: 'Aprovar' })).not.toBeInTheDocument();
  });

  it('exibe mensagem de rejeitado sem link de download', () => {
    renderPanel({ result: { ...baseResult, status: 'rejeitado' } });
    expect(screen.getByText(/rejeitou a sugestão/)).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Baixar PDF' })).not.toBeInTheDocument();
  });
});
