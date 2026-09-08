"""6 nós do grafo LangGraph.

Cada nó recebe o estado e devolve o estado atualizado. Os agentes
(`triar`, `sintetizar`, `validar`) já obtêm o LLM internamente via
`get_llm()`, então o `llm_client` passado pelo workflow é aceito apenas
por compatibilidade de assinatura.
"""
import hashlib


EMERGENCY_KEYWORDS = [
    "dor torácica", "infarto", "avc", "derrame", "dispneia",
    "sepse", "choque", "parada cardíaca", "anafilaxia",
    "sangramento ativo", "hemorragia",
]


def detect_emergency(relato: str) -> bool:
    return any(kw in relato.lower() for kw in EMERGENCY_KEYWORDS)


def node_triagem(state, llm_client=None):
    from src.agents.triagem import triar

    triagem_result = triar(state["relato_inicial"])
    return {
        **state,
        "triagem": triagem_result,
        "rag_pmc_chunks": [],
        "rag_interno_chunks": [],
    }


def node_retrieval(state, retriever):
    query = state["relato_inicial"]
    rag_interno = []
    if retriever is not None:
        try:
            rag_interno = retriever.retrieve_interno(query, k=6)
        except Exception as e:  # noqa: BLE001
            print(f"⚠️  retrieval falhou: {e}")
            rag_interno = []
    return {
        **state,
        "rag_pmc_chunks": [],
        "rag_interno_chunks": rag_interno,
    }


def node_sintese(state, llm_client=None):
    from src.agents.sintese import sintetizar

    sintese_result = sintetizar(
        state["relato_inicial"],
        state.get("rag_pmc_chunks", []),
        state.get("rag_interno_chunks", []),
    )
    return {**state, "sintese": sintese_result}


def node_validacao(state, llm_client=None):
    from src.agents.validacao import validar

    validated = validar(state["sintese"], state["triagem"], llm_client)
    return {**state, "validacao": validated}


def node_hitl(state):
    """Pausa aguardando decisão humana."""
    return state


def node_gerar_docs(state, doc_generator):
    if state.get("medico_decisao") == "rejeitado":
        return state

    sintese = state.get("validacao") or state.get("sintese") or {}
    paciente = state.get("dados_paciente") or {}
    dados = {
        "paciente": paciente.get("nome", "Não informado"),
        "idade": paciente.get("idade", "—"),
        "sexo": paciente.get("sexo", "—"),
        "medico": paciente.get("medico", "Dr(a). Responsável"),
        "crm": paciente.get("crm", "000000-UF"),
        "queixa_principal": state.get("texto_editado") or state.get("relato_inicial", ""),
        "exame_fisico": "Conforme avaliação clínica.",
        "hipoteses": sintese.get("hipoteses", []),
        "exames_sugeridos": sintese.get("exames_sugeridos", []),
        "medicacoes_sugeridas": sintese.get("medicacoes_sugeridas", []),
        "observacoes": sintese.get("observacoes", ""),
    }

    doc_path = doc_generator.gerar_prontuario(dados)
    with open(doc_path, "rb") as f:
        doc_hash = hashlib.sha256(f.read()).hexdigest()
    return {
        **state,
        "documento_final": doc_path,
        "hash_documento": doc_hash,
    }
