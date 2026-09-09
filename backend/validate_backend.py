import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("LLM_MOCK", "1")

from fastapi.testclient import TestClient
from src.api.app import app


def main() -> None:
    client = TestClient(app)
    health = client.get("/health")
    login = client.post("/api/auth/login", json={"username": "medico", "password": "demo123"})
    consulta = client.post(
        "/api/consulta",
        json={
            "relato": "Paciente relata febre e tosse há 3 dias, sem dispneia.",
            "paciente": {"nome": "Ana", "idade": "34", "sexo": "F"},
            "medico": {"nome": "Dr. Teste", "crm": "12345"},
        },
    )

    print(f"health={health.status_code}")
    print(f"login={login.status_code}")
    print(f"consulta={consulta.status_code}")
    print(f"consulta_json={consulta.json().get('status')}")


if __name__ == "__main__":
    main()
