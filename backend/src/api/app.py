from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from langgraph.types import Command
from pydantic import BaseModel, Field

from src.docs.generator import DocumentGenerator
from src.graph.workflow import criar_workflow
from src.llm.client import get_llm
from src.llm.langchain_client import get_langchain_llm
from src.rag.retriever import Retriever
from src.logging.audit import init_db, log_event
from src.logging.schemas import (
    AuditEvent,
    DocumentGeneratedEvent,
    HITLDecisionEvent,
    LLMCallEvent,
    RAGRetrievalEvent,
)


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
    paciente_id: Optional[str] = None
    paciente: Optional[Dict[str, Any]] = None
    medico: Optional[Dict[str, Any]] = None


class DecisaoRequest(BaseModel):
    decisao: Literal["aprovado", "editado", "rejeitado"]
    texto_editado: Optional[str] = None


class ConsultationResponse(BaseModel):
    session_id: str
    status: str
    triagem: Dict[str, Any]
    rag: List[Dict[str, Any]]
    sintese: Dict[str, Any]
    documento: Optional[str] = None
    hash_documento: Optional[str] = None
    auth_valid: bool


def _log_etapa(session_id: str, user_id: str, etapa: str, parcial: Dict[str, Any]) -> None:
    """Loga um evento de auditoria por etapa do grafo (triagem, retrieval, etc)."""
    try:
        if etapa == "triagem":
            evt = LLMCallEvent(
                event_type="triagem", session_id=session_id, user_id=user_id,
                agent="triagem", model="biomistral-lora",
                output_preview=str(parcial.get("triagem", ""))[:500],
                metadata={"categoria": (parcial.get("triagem") or {}).get("categoria")},
            )
        elif etapa == "contexto_paciente":
            historico = parcial.get("historico_paciente") or {}
            evt = AuditEvent(
                event_type="contexto_paciente", session_id=session_id, user_id=user_id,
                metadata={"paciente_encontrado": bool(historico)},
            )
        elif etapa == "retrieval":
            chunks = parcial.get("rag_interno_chunks") or []
            evt = RAGRetrievalEvent(
                event_type="retrieval", session_id=session_id, user_id=user_id,
                rag_source="chatbulario+cid10+synthetic", n_chunks=len(chunks),
                metadata={"fontes": [c.get("source") for c in chunks[:5]]},
            )
        elif etapa == "sintese":
            evt = LLMCallEvent(
                event_type="sintese", session_id=session_id, user_id=user_id,
                agent="sintese", model="biomistral-lora",
                output_preview=str(parcial.get("sintese", ""))[:500],
            )
        elif etapa == "validacao":
            validacao = parcial.get("validacao") or {}
            evt = AuditEvent(
                event_type="validacao", session_id=session_id, user_id=user_id,
                metadata={"tem_disclaimer": bool(validacao.get("disclaimer"))},
            )
        elif etapa == "hitl":
            evt = HITLDecisionEvent(
                event_type="hitl_decisao", session_id=session_id, user_id=user_id,
                action=parcial.get("medico_decisao") or "pendente",
                texto_editado=parcial.get("texto_editado"),
            )
        elif etapa == "gerar_docs":
            evt = DocumentGeneratedEvent(
                event_type="documento_gerado", session_id=session_id, user_id=user_id,
                document_type="prontuario",
                file_path=parcial.get("documento_final") or "",
                sha256=parcial.get("hash_documento") or "",
            )
        else:
            evt = AuditEvent(event_type=etapa, session_id=session_id, user_id=user_id)

        log_event(evt, APP_ROOT / "audit.db")
    except Exception:
        pass


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
    erros_iniciais: List[str] = []

    try:
        llm_client = get_langchain_llm()
    except Exception as exc:
        llm_client = None
        erros_iniciais.append(f"LLM indisponível: {exc}")

    try:
        retriever = Retriever(chroma_dir=APP_ROOT / "data" / "processed" / "chroma_index")
    except Exception as exc:
        retriever = None
        erros_iniciais.append(f"RAG indisponível: {exc}")

    doc_generator = DocumentGenerator(output_dir=str(APP_ROOT / "data" / "documents"))

    state = {
        "relato_inicial": relato,
        "dados_paciente": {**paciente, **medico},
        "paciente_id": payload.paciente_id,
        "historico_paciente": None,
        "triagem": None,
        "sintese": None,
        "validacao": None,
        "rag_pmc_chunks": [],
        "rag_interno_chunks": [],
        "medico_decisao": None,
        "texto_editado": relato,
        "documento_final": None,
        "hash_documento": None,
        "session_id": session_id,
        "timestamp_inicio": datetime.now(timezone.utc).isoformat(),
        "erros": erros_iniciais,
    }
    medico_nome = medico.get("nome", "medico")

    # Executa o grafo LangGraph compilado (triagem -> contexto_paciente ->
    # retrieval -> sintese -> validacao -> hitl) via stream (1 evento de
    # auditoria por etapa concluida — ver _log_etapa). O grafo PARA sozinho
    # dentro do no `hitl` (interrupt()): sem decisao do medico, `gerar_docs`
    # nunca roda e nenhum documento e emitido nessa chamada.
    grafo = criar_workflow(llm_client, retriever, doc_generator)
    config = {"configurable": {"thread_id": session_id}}

    for update in grafo.stream(state, config=config, stream_mode="updates"):
        for etapa, parcial in update.items():
            if etapa == "__interrupt__":
                continue
            _log_etapa(session_id, medico_nome, etapa, parcial)

    resultado = grafo.get_state(config).values

    rag_result = resultado.get("rag_interno_chunks", [])
    triagem_result = resultado.get("triagem") or {}
    sintese_result = resultado.get("validacao") or resultado.get("sintese") or {}

    return ConsultationResponse(
        session_id=session_id,
        status="aguardando_validacao",
        triagem=triagem_result,
        rag=[{"source": item.get("source", "chatbulario"), "content": item.get("content", "")} for item in rag_result[:5]],
        sintese=sintese_result,
        documento=None,
        hash_documento=None,
        auth_valid=True,
    )


@app.post("/api/consulta/{session_id}/decisao", response_model=ConsultationResponse)
def decisao_medica(session_id: str, payload: DecisaoRequest) -> ConsultationResponse:
    """Recebe a decisão do médico (aprovar/editar/rejeitar) e retoma o grafo pausado.

    Só a partir daqui o documento é gerado — e só se a decisão for
    "aprovado" ou "editado" (ver `pos_hitl` em src/graph/workflow.py).
    """
    doc_generator = DocumentGenerator(output_dir=str(APP_ROOT / "data" / "documents"))
    grafo = criar_workflow(None, None, doc_generator)
    config = {"configurable": {"thread_id": session_id}}

    snapshot = grafo.get_state(config)
    if not snapshot.values:
        raise HTTPException(status_code=404, detail="Sessão de consulta não encontrada ou expirada.")
    if not snapshot.next:
        raise HTTPException(status_code=409, detail="Essa consulta já foi decidida.")

    medico_nome = (snapshot.values.get("dados_paciente") or {}).get("nome", "medico")

    for update in grafo.stream(
        Command(resume={"decisao": payload.decisao, "texto_editado": payload.texto_editado}),
        config=config,
        stream_mode="updates",
    ):
        for etapa, parcial in update.items():
            if etapa == "__interrupt__":
                continue
            _log_etapa(session_id, medico_nome, etapa, parcial)

    resultado = grafo.get_state(config).values

    errors = resultado.get("erros", [])
    rag_result = resultado.get("rag_interno_chunks", [])
    triagem_result = resultado.get("triagem") or {}
    sintese_result = resultado.get("validacao") or resultado.get("sintese") or {}
    documento = resultado.get("documento_final")
    hash_documento = resultado.get("hash_documento")

    if payload.decisao == "rejeitado":
        status_final = "rejeitado"
    elif errors:
        status_final = "partial"
    else:
        status_final = "ok"

    return ConsultationResponse(
        session_id=session_id,
        status=status_final,
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
