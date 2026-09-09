import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginCard from './LoginCard';

function renderLoginCard(overrides = {}) {
  const props = {
    username: 'medico',
    password: 'demo123',
    onUsernameChange: vi.fn(),
    onPasswordChange: vi.fn(),
    onSubmit: vi.fn(),
    loading: false,
    disabled: false,
    error: '',
    ...overrides,
  };
  render(<LoginCard {...props} />);
  return props;
}

describe('LoginCard', () => {
  it('exibe os valores atuais de usuario e senha', () => {
    renderLoginCard();
    expect(screen.getByLabelText('Usuário')).toHaveValue('medico');
    expect(screen.getByLabelText('Senha')).toHaveValue('demo123');
  });

  it('chama onSubmit ao clicar em Entrar', async () => {
    const user = userEvent.setup();
    const props = renderLoginCard();

    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    expect(props.onSubmit).toHaveBeenCalledTimes(1);
  });

  it('desabilita o botao quando disabled=true', () => {
    renderLoginCard({ disabled: true });
    expect(screen.getByRole('button', { name: 'Entrar' })).toBeDisabled();
  });

  it('mostra "Entrando..." e desabilita o botao durante loading', () => {
    renderLoginCard({ loading: true });
    expect(screen.getByRole('button', { name: 'Entrando...' })).toBeDisabled();
  });

  it('exibe mensagem de erro quando presente', () => {
    renderLoginCard({ error: 'Credenciais inválidas' });
    expect(screen.getByText('Credenciais inválidas')).toBeInTheDocument();
  });

  it('nao exibe a dica de credenciais quando disabled=true', () => {
    renderLoginCard({ disabled: true });
    expect(screen.queryByText('Use: medico / demo123')).not.toBeInTheDocument();
  });
});
