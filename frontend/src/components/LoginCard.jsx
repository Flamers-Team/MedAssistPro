export default function LoginCard({
  username,
  password,
  onUsernameChange,
  onPasswordChange,
  onSubmit,
  loading,
  disabled,
  error,
}) {
  return (
    <div className="login-shell">
      <div className="login-card">
        <h1>Assistente Médico Inteligente</h1>
        <p>Login do médico</p>

        <label htmlFor="login-username">Usuário</label>
        <input id="login-username" value={username} onChange={onUsernameChange} />

        <label htmlFor="login-password">Senha</label>
        <input id="login-password" type="password" value={password} onChange={onPasswordChange} />

        <button className="primary full" onClick={onSubmit} disabled={disabled || loading}>
          {loading ? 'Entrando...' : 'Entrar'}
        </button>

        {error && <small className="error-text">{error}</small>}
        {!disabled && <small className="hint">Use: medico / demo123</small>}
      </div>
    </div>
  );
}
