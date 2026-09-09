import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ConsultaPanel from './ConsultaPanel';

const baseResult = {
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

  it('exibe o link de download quando ha documento gerado', () => {
    renderPanel({
      result: { ...baseResult, documento: 'prontuario_123.pdf', downloadUrl: 'http://x/api/download?path=abc' },
    });
    expect(screen.getByRole('link', { name: 'Baixar PDF' })).toHaveAttribute(
      'href',
      'http://x/api/download?path=abc'
    );
  });

  it('nao exibe link de download quando nao ha documento', () => {
    renderPanel();
    expect(screen.queryByRole('link', { name: 'Baixar PDF' })).not.toBeInTheDocument();
  });

  it('exibe mensagem de erro quando presente', () => {
    renderPanel({ error: 'Erro ao iniciar consulta' });
    expect(screen.getByText('Erro ao iniciar consulta')).toBeInTheDocument();
  });
});
