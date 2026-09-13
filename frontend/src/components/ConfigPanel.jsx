const systemInfo = [
  ['Modelo', 'BioMistral-medquad-lora'],
  ['Status do RAG', 'Disponível quando índice existir'],
  ['Banco', 'audit.db'],
  ['Documentos', 'data/documents'],
  ['Frontend', 'React + Vite'],
  ['GitHub', 'Flamers-Team/MedAssistPro'],
];

export default function ConfigPanel() {
  return (
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
  );
}
