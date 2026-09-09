export default function ConsultaPanel({
  relato,
  setRelato,
  loading,
  error,
  onProcess,
  onClear,
  result,
}) {
  return (
    <div className="panel-grid two-cols">
      <div className="panel">
        <h3>Consulta</h3>
        <label>Relato do paciente</label>
        <textarea value={relato} onChange={(e) => setRelato(e.target.value)} rows={12} />
        <div className="button-row">
          <button className="primary" onClick={onProcess} disabled={loading}>
            {loading ? 'Processando...' : 'Iniciar consulta'}
          </button>
          <button className="secondary" onClick={onClear}>Limpar</button>
        </div>
        {error && <small className="error-text">{error}</small>}
      </div>

      <div className="panel">
        <h3>Resultados</h3>

        <div className="result-box">
          <h4>🚨 Triagem</h4>
          <p><strong>Categoria:</strong> {result.triagem.categoria}</p>
          <p><strong>Justificativa:</strong> {result.triagem.justificativa}</p>
          <p><strong>Red flags:</strong> {(result.triagem.red_flags || []).join(', ') || 'Nenhum'}</p>
          <p><strong>Confiança:</strong> {typeof result.triagem.confianca === 'number' ? `${(result.triagem.confianca * 100).toFixed(0)}%` : result.triagem.confianca || '—'}</p>
        </div>

        <div className="result-box">
          <h4>📚 RAG</h4>
          <ul>
            {(result.rag || []).length > 0 ? result.rag.map((item, idx) => <li key={idx}>{item}</li>) : <li>Nenhum contexto recuperado.</li>}
          </ul>
        </div>

        <div className="result-box">
          <h4>🧠 Síntese</h4>
          <p>{result.sintese.resumo}</p>
          <p><strong>Exames:</strong> {(result.sintese.exames || []).join(', ') || 'Nenhum'}</p>
          <p><strong>Medicações:</strong> {(result.sintese.medicamentos || []).join(', ') || 'Nenhuma'}</p>
          {result.documento && (
            <p>
              <strong>Documento:</strong>{' '}
              <a href={result.downloadUrl}>Baixar PDF</a>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
