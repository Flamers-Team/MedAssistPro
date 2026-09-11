"""Monta o StateGraph completo com os nós do assistente."""
import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, END
from src.graph.state import ConversationState
from src.graph.nodes import (
    node_triagem, node_contexto_paciente, node_retrieval, node_sintese,
    node_validacao, node_hitl, node_gerar_docs,
)

# Checkpointer SQLite compartilhado: guarda o estado do grafo entre a
# chamada que pausa em `hitl` (POST /api/consulta) e a que retoma com a
# decisão do médico (POST /api/consulta/{session_id}/decisao). Precisa
# sobreviver entre requisições HTTP diferentes, por isso é SQLite (não
# InMemorySaver) e vive em data/processed/, ao lado do audit.db.
_CHECKPOINT_DB_PATH = Path(__file__).resolve().parents[3] / "data" / "processed" / "checkpoints.db"
_CHECKPOINT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
_checkpointer = SqliteSaver(sqlite3.connect(str(_CHECKPOINT_DB_PATH), check_same_thread=False))


def criar_workflow(llm_client, retriever, doc_generator):
    """Monta e retorna o StateGraph compilado, com checkpointer para HITL real."""
    workflow = StateGraph(ConversationState)

    workflow.add_node("triagem", lambda s: node_triagem(s, llm_client))
    workflow.add_node("contexto_paciente", node_contexto_paciente)
    workflow.add_node("retrieval", lambda s: node_retrieval(s, retriever))
    workflow.add_node("sintese", lambda s: node_sintese(s, llm_client))
    workflow.add_node("validacao", lambda s: node_validacao(s, llm_client))
    workflow.add_node("hitl", node_hitl)
    workflow.add_node("gerar_docs", lambda s: node_gerar_docs(s, doc_generator))

    workflow.set_entry_point("triagem")
    workflow.add_edge("triagem", "contexto_paciente")
    workflow.add_edge("contexto_paciente", "retrieval")
    workflow.add_edge("retrieval", "sintese")
    workflow.add_edge("sintese", "validacao")
    workflow.add_edge("validacao", "hitl")

    def pos_hitl(state):
        decisao = state.get("medico_decisao")
        if decisao in ("aprovado", "editado"):
            return "gerar_docs"
        return END

    workflow.add_conditional_edges("hitl", pos_hitl, {
        "gerar_docs": "gerar_docs",
        END: END,
    })
    workflow.add_edge("gerar_docs", END)

    return workflow.compile(checkpointer=_checkpointer)