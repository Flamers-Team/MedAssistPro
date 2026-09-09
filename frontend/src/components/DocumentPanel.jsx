export default function DocumentPanel({ documents }) {
  return (
    <div className="panel">
      <h3>Documentos gerados</h3>
      <div className="doc-list">
        {documents.length > 0 ? documents.map((doc, idx) => (
          <div key={idx} className="doc-item">
            <div>
              <strong>{doc.name}</strong>
              <small>{doc.date}</small>
            </div>
            <span>{doc.size}</span>
          </div>
        )) : (
          <p>Nenhum documento gerado ainda.</p>
        )}
      </div>
    </div>
  );
}
