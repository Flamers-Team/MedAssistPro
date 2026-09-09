from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.docs.generator import DocumentGenerator
from src.graph.nodes import node_triagem, node_retrieval, node_sintese, node_validacao
from src.llm.client import get_llm
from src.rag.retriever import Retriever
from src.logging.audit import init_db, log_event


APP_ROOT = Path(__file__).resolve().parents[3]

def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class ConsultationRequest(BaseModel):
    relato: str = Field(..., min_length=10)
    paciente: Optional[Dict[str, Any]] = None
    medico: Optional[Dict[str, Any]] = None


class ConsultationResponse(BaseModel):
    session_id: str
    status: str
    triagem: Dict[str, Any]
    rag: List[Dict[str, Any]]
    sintese: Dict[str, Any]
    documento: Optional[str] = None
    hash_documento: Optional[str] = None
    auth_valid: bool


app = FastAPI(title="Assistente Médico IA", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):(3000|3001|5173)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    try:
        init_db(APP_ROOT / "audit.db")
    except Exception:
        pass

    try:
        os.environ.setdefault("LLM_MOCK", "1")
        get_llm()
    except Exception:
        pass

    try:
        Retriever(chroma_dir=APP_ROOT / "data" / "processed" / "chroma_index")
    except Exception:
        pass


@app.get("/health")
def healthcheck() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "assistente-medico-ia",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/auth/login")
def login(payload: LoginRequest) -> Dict[str, Any]:
    valid = payload.username == "medico" and payload.password == "demo123"
    return {
        "success": valid,
        "message": "Login validado" if valid else "Credenciais inválidas",
        "username": payload.username,
    }


@app.post("/api/consulta", response_model=ConsultationResponse)
def consulta(payload: ConsultationRequest) -> ConsultationResponse:
    relato = (payload.relato or "").strip()
    if not relato:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Relato do paciente não pode estar vazio.")

    session_id = str(uuid.uuid4())
    paciente = payload.paciente or {"nome": "Paciente", "idade": "—", "sexo": "—"}
    medico = payload.medico or {"nome": "Dr(a). Responsável", "crm": "000000-UF"}
    errors: List[str] = []

    try:
        llm_client = get_llm()
    except Exception as exc:
        llm_client = None
        errors.append(f"LLM indisponível: {exc}")

    try:
        retriever = Retriever(chroma_dir=APP_ROOT / "data" / "processed" / "chroma_index")
    except Exception as exc:
        retriever = None
        errors.append(f"RAG indisponível: {exc}")

    doc_generator = DocumentGenerator(output_dir=str(APP_ROOT / "data" / "documents"))

    state = {
        "relato_inicial": relato,
        "dados_paciente": {**paciente, **medico},
        "triagem": None,
        "sintese": None,
        "validacao": None,
        "rag_pmc_chunks": [],
        "rag_interno_chunks": [],
        "medico_decisao": "aprovado",
        "texto_editado": relato,
        "documento_final": None,
        "hash_documento": None,
        "session_id": session_id,
        "timestamp_inicio": datetime.now(timezone.utc).isoformat(),
        "erros": [],
    }

    try:
        state = node_triagem(state, llm_client)
    except Exception as exc:
        errors.append(f"Triagem falhou: {exc}")
        state["triagem"] = {"categoria": "ROTINA", "justificativa": "Triagem em modo fallback", "red_flags": [], "confianca": "baixa"}

    try:
        state = node_retrieval(state, retriever)
    except Exception as exc:
        errors.append(f"Retrieval falhou: {exc}")
        state["rag_interno_chunks"] = []

    try:
        state = node_sintese(state, llm_client)
    except Exception as exc:
        errors.append(f"Síntese falhou: {exc}")
        state["sintese"] = {"hipoteses": [], "exames_sugeridos": [], "medicacoes_sugeridas": [], "observacoes": "Síntese em modo fallback devido a indisponibilidade do LLM."}

    try:
        state = node_validacao(state, llm_client)
    except Exception as exc:
        errors.append(f"Validação falhou: {exc}")
        state["validacao"] = state.get("sintese") or {"hipoteses": [], "exames_sugeridos": [], "medicacoes_sugeridas": [], "observacoes": "Validação em modo fallback."}

    rag_result = state.get("rag_interno_chunks", [])
    triagem_result = state.get("triagem") or {"categoria": "ROTINA", "justificativa": "Sem resultado disponível", "red_flags": [], "confianca": "baixa"}
    sintese_result = state.get("validacao") or state.get("sintese") or {"hipoteses": [], "exames_sugeridos": [], "medicacoes_sugeridas": [], "observacoes": "Sem síntese disponível."}

    dados_pdf = {
        "paciente": paciente.get("nome", "Não informado"),
        "idade": paciente.get("idade", "—"),
        "sexo": paciente.get("sexo", "—"),
        "medico": medico.get("nome", "Dr(a). Responsável"),
        "crm": medico.get("crm", "000000-UF"),
        "queixa_principal": relato,
        "exame_fisico": "Conforme avaliação clínica.",
        "hipoteses": sintese_result.get("hipoteses", []),
        "exames_sugeridos": sintese_result.get("exames_sugeridos", []),
        "medicacoes_sugeridas": sintese_result.get("medicacoes_sugeridas", []),
        "observacoes": sintese_result.get("observacoes", ""),
    }

    documento = None
    hash_documento = None
    try:
        documento = doc_generator.gerar_prontuario(dados_pdf)
        with open(documento, "rb") as fh:
            import hashlib
            hash_documento = hashlib.sha256(fh.read()).hexdigest()
    except Exception as exc:
        errors.append(f"Geração de PDF falhou: {exc}")
        documento = None
        hash_documento = None

    try:
        log_event(type("Evt", (), {
            "to_dict": lambda self: {
                "event_type": "consulta",
                "session_id": session_id,
                "user_id": medico.get("nome", "medico"),
                "agent": "api",
                "model": "mock",
                "input_preview": relato[:500],
                "output_preview": str(sintese_result)[:500],
                "metadata": {"categoria": triagem_result.get("categoria"), "errors": errors[:3]},
            }
        })(), APP_ROOT / "audit.db")
    except Exception:
        pass

    return ConsultationResponse(
        session_id=session_id,
        status="partial" if errors else "ok",
        triagem=triagem_result,
        rag=[{"source": item.get("source", "chatbulario"), "content": item.get("content", "")} for item in rag_result[:5]],
        sintese=sintese_result,
        documento=documento,
        hash_documento=hash_documento,
        auth_valid=True,
    )


@app.get("/api/auditoria")
def auditoria() -> Dict[str, Any]:
    db_path = APP_ROOT / "audit.db"
    if not db_path.exists():
        return {"events": [], "total": 0}

    import sqlite3

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT timestamp, event_type, session_id, agent, user_id, metadata FROM events ORDER BY id DESC LIMIT 20"
    ).fetchall()
    conn.close()

    return {
        "events": [dict(r) for r in rows],
        "total": len(rows),
    }


@app.get("/api/documentos")
def documentos() -> Dict[str, Any]:
    docs_dir = APP_ROOT / "data" / "documents"
    files = []
    if docs_dir.exists():
        for item in sorted(docs_dir.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True):
            files.append({
                "name": item.name,
                "size": f"{item.stat().st_size / 1024:.1f} KB",
                "date": datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                "path": str(item),
            })
    return {"documents": files}


@app.get("/api/download")
def download_document(path: str = Query(..., description="Caminho absoluto do arquivo PDF")) -> FileResponse:
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(file_path, media_type="application/pdf", filename=file_path.name)
