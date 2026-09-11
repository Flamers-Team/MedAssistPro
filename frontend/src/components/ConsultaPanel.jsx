import { useState } from 'react';

export default function ConsultaPanel({
  relato,
  setRelato,
  loading,
  error,
  onProcess,
  onClear,
  onDecidir,
  result,
}) {
  const [mostrarEdicao, setMostrarEdicao] = useState(false);
  const [textoEditado, setTextoEditado] = useState('');

  const aguardandoValidacao = result.status === 'aguardando_validacao';

  const aprovar = () => onDecidir('aprovado');
  const rejeitar = () => onDecidir('rejeitado');
  const confirmarEdicao = () => {
    onDecidir('editado', textoEditado);
    setMostrarEdicao(false);
  };

  return (
    <div className="panel-grid two-cols">
      <div className="panel">
        <h3>Consulta</h3>
        <label htmlFor="relato-paciente">Relato do paciente</label>
        <textarea id="relato-paciente" value={relato} onChange={(e) => setRelato(e.target.value)} rows={12} />
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
        </div>

        {aguardandoValidacao && (
          <div className="result-box">
            <h4>⚕️ Validação médica obrigatória</h4>
            <p>Nenhum documento foi gerado ainda. Revise a síntese acima antes de decidir.</p>

            {!mostrarEdicao ? (
              <div className="button-row">
                <button className="primary" onClick={aprovar} disabled={loading}>Aprovar</button>
                <button className="secondary" onClick={() => { setTextoEditado(relato); setMostrarEdicao(true); }} disabled={loading}>
                  Editar e aprovar
                </button>
                <button className="secondary" onClick={rejeitar} disabled={loading}>Rejeitar</button>
              </div>
            ) : (
              <>
                <label htmlFor="texto-editado">Texto editado (substitui a queixa principal no documento)</label>
                <textarea id="texto-editado" value={textoEditado} onChange={(e) => setTextoEditado(e.target.value)} rows={6} />
                <div className="button-row">
                  <button className="primary" onClick={confirmarEdicao} disabled={loading}>Confirmar edição e aprovar</button>
                  <button className="secondary" onClick={() => setMostrarEdicao(false)} disabled={loading}>Cancelar</button>
                </div>
              </>
            )}
          </div>
        )}

        {result.status === 'rejeitado' && (
          <div className="result-box">
            <h4>✖️ Rejeitado</h4>
            <p>O médico rejeitou a sugestão. Nenhum documento foi gerado.</p>
          </div>
        )}

        {(result.status === 'ok' || result.status === 'partial') && result.documento && (
          <div className="result-box">
            <h4>✅ Aprovado</h4>
            <p>
              <strong>Documento:</strong>{' '}
              <a href={result.downloadUrl}>Baixar PDF</a>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
