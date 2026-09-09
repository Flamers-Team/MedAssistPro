import os, traceback
os.environ['PYTHONPATH'] = r'c:\dev\TechChallenge3\Techchalleng3'
os.environ['LLM_MOCK'] = '1'
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)
try:
    r = client.post('/api/consulta', json={
        'relato': 'Paciente de 45 anos relata dor torácica há 3 horas, sudorese, ansiedade e pressão arterial 150/90.',
        'paciente': {'nome': 'Maria Silva', 'idade': 45, 'sexo': 'F'},
        'medico': {'nome': 'Dr. João', 'crm': '12345-SP'}
    })
    print('STATUS', r.status_code)
    print(r.text)
except Exception:
    traceback.print_exc()
