"""Base de dados estruturada de prontuários (sintética) para consulta por paciente.

SQLite local em data/processed/prontuarios.db, criado e populado
automaticamente com pacientes sintéticos na primeira vez que for usado.
Usada pela tool do LangChain em src/graph/tools.py para contextualizar
a síntese clínica com o histórico do paciente.

Uso:
    from src.data.prontuarios import ProntuarioStore

    store = ProntuarioStore()
    prontuario = store.buscar_por_id("PAC-0001")
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = Path(__file__).resolve().parents[3] / "data" / "processed" / "prontuarios.db"

# Pacientes sinteticos — nenhum dado real. Servem para demonstrar a consulta
# estruturada por paciente pedida no enunciado (LangChain tool + grafo).
SEED_PACIENTES: List[Dict[str, Any]] = [
    {
        "paciente_id": "PAC-0001",
        "nome": "Ana Beatriz Souza",
        "idade": 34,
        "sexo": "F",
        "alergias": ["Dipirona (rash cutâneo leve)"],
        "condicoes_cronicas": [],
        "historico": [
            {
                "data": "2026-03-12",
                "motivo": "Dor torácica atípica",
                "diagnostico": "Ansiedade / DRGE",
                "medicacoes": ["Omeprazol 20mg"],
            },
            {
                "data": "2025-11-02",
                "motivo": "Cefaleia tensional recorrente",
                "diagnostico": "Cefaleia tensional",
                "medicacoes": ["Dipirona 500mg"],
            },
        ],
    },
    {
        "paciente_id": "PAC-0002",
        "nome": "Carlos Eduardo Lima",
        "idade": 61,
        "sexo": "M",
        "alergias": [],
        "condicoes_cronicas": ["Hipertensão arterial", "Diabetes tipo 2"],
        "historico": [
            {
                "data": "2026-01-20",
                "motivo": "Dor torácica ao esforço",
                "diagnostico": "Angina estável — encaminhado ao cardiologista",
                "medicacoes": ["AAS 100mg", "Atenolol 25mg"],
            },
            {
                "data": "2025-08-15",
                "motivo": "Consulta de rotina — controle glicêmico",
                "diagnostico": "Diabetes tipo 2 controlado",
                "medicacoes": ["Metformina 850mg"],
            },
        ],
    },
    {
        "paciente_id": "PAC-0003",
        "nome": "Mariana Costa Ferreira",
        "idade": 8,
        "sexo": "F",
        "alergias": ["Amoxicilina (urticária)"],
        "condicoes_cronicas": ["Asma leve intermitente"],
        "historico": [
            {
                "data": "2026-02-05",
                "motivo": "Tosse e chiado no peito",
                "diagnostico": "Crise asmática leve",
                "medicacoes": ["Salbutamol spray (resgate)"],
            },
        ],
    },
    {
        "paciente_id": "PAC-0004",
        "nome": "José Roberto Almeida",
        "idade": 45,
        "sexo": "M",
        "alergias": [],
        "condicoes_cronicas": [],
        "historico": [],
    },
]


class ProntuarioStore:
    """Wrapper de acesso à base estruturada de prontuários (SQLite)."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pacientes (
                    paciente_id TEXT PRIMARY KEY,
                    nome TEXT NOT NULL,
                    idade INTEGER,
                    sexo TEXT,
                    alergias TEXT,
                    condicoes_cronicas TEXT,
                    historico TEXT
                )
                """
            )
            count = conn.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0]
            if count == 0:
                self._seed(conn)

    def _seed(self, conn: sqlite3.Connection) -> None:
        for p in SEED_PACIENTES:
            conn.execute(
                """
                INSERT INTO pacientes
                    (paciente_id, nome, idade, sexo, alergias, condicoes_cronicas, historico)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    p["paciente_id"],
                    p["nome"],
                    p["idade"],
                    p["sexo"],
                    json.dumps(p.get("alergias", []), ensure_ascii=False),
                    json.dumps(p.get("condicoes_cronicas", []), ensure_ascii=False),
                    json.dumps(p.get("historico", []), ensure_ascii=False),
                ),
            )
        conn.commit()

    def buscar_por_id(self, paciente_id: str) -> Optional[Dict[str, Any]]:
        """Busca o prontuário estruturado de um paciente. Retorna None se não existir."""
        if not paciente_id or not paciente_id.strip():
            return None

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM pacientes WHERE paciente_id = ?", (paciente_id.strip(),)
            ).fetchone()

        if row is None:
            return None

        return {
            "paciente_id": row["paciente_id"],
            "nome": row["nome"],
            "idade": row["idade"],
            "sexo": row["sexo"],
            "alergias": json.loads(row["alergias"] or "[]"),
            "condicoes_cronicas": json.loads(row["condicoes_cronicas"] or "[]"),
            "historico": json.loads(row["historico"] or "[]"),
        }

    def listar_ids(self) -> List[str]:
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute("SELECT paciente_id FROM pacientes ORDER BY paciente_id").fetchall()
        return [r[0] for r in rows]
