from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)

login = client.post('/api/auth/login', json={'username': 'medico', 'password': 'demo123'})
print('LOGIN_STATUS', login.status_code)
print('LOGIN_BODY', login.json())

resp = client.post('/api/consulta', json={
    'relato': 'Paciente de 45 anos relata dor torácica há 3 horas, sudorese, ansiedade e pressão arterial 150/90.',
    'paciente': {'nome': 'Maria Silva', 'idade': 45, 'sexo': 'F'},
    'medico': {'nome': 'Dr. João', 'crm': '12345-SP'}
})
print('CONSULTA_STATUS', resp.status_code)
body = resp.json()
print('CONSULTA_KEYS', sorted(body.keys()))
print('TRIAGEM', body.get('triagem'))
print('HAS_DOC', bool(body.get('documento')))
print('RAG_COUNT', len(body.get('rag', [])))
print('SINTES', body.get('sintese'))
print('AUDITORIA_STATUS', client.get('/api/auditoria').status_code)
print('DOCUMENTOS_STATUS', client.get('/api/documentos').status_code)
