"""Nós do grafo LangGraph.

Cada nó recebe o estado e devolve o estado atualizado. Cada nó captura
suas próprias exceções e degrada para um resultado de fallback seguro,
em vez de deixar `criar_workflow(...).invoke(state)` abortar inteiro —
assim a API consegue rodar o grafo compilado de ponta a ponta com uma
única chamada e ainda devolver resultado parcial se uma etapa falhar
(ex.: RAG ou LLM indisponível).
"""
import hashlib


EMERGENCY_KEYWORDS = [
    "dor torácica", "infarto", "avc", "derrame", "dispneia",
    "sepse", "choque", "parada cardíaca", "anafilaxia",
    "sangramento ativo", "hemorragia",
]

TRIAGEM_FALLBACK = {
    "categoria": "ROTINA",
    "justificativa": "Triagem em modo fallback",
    "red_flags": [],
    "confianca": "baixa",
}

SINTESE_FALLBACK = {
    "hipoteses": [],
    "exames_sugeridos": [],
    "medicacoes_sugeridas": [],
    "observacoes": "Síntese em modo fallback devido a indisponibilidade do LLM.",
}


def detect_emergency(relato: str) -> bool:
    return any(kw in relato.lower() for kw in EMERGENCY_KEYWORDS)


def node_triagem(state, llm_client=None):
    from src.agents.triagem import triar

    erros = list(state.get("erros", []))
    try:
        triagem_result = triar(state["relato_inicial"], llm_client)
    except Exception as exc:  # noqa: BLE001
        erros.append(f"Triagem falhou: {exc}")
        triagem_result = dict(TRIAGEM_FALLBACK)

    return {
        **state,
        "triagem": triagem_result,
        "rag_pmc_chunks": [],
        "rag_interno_chunks": [],
        "erros": erros,
    }


def node_contexto_paciente(state):
    """Consulta o prontuário estruturado do paciente (tool do LangChain)."""
    from src.graph.tools import consultar_prontuario

    paciente_id = state.get("paciente_id")
    erros = list(state.get("erros", []))
    historico = {}
    if paciente_id:
        try:
            historico = consultar_prontuario.invoke({"paciente_id": paciente_id}) or {}
        except Exception as exc:  # noqa: BLE001
            erros.append(f"Consulta ao prontuário falhou: {exc}")

    return {**state, "historico_paciente": historico, "erros": erros}


def node_retrieval(state, retriever):
    query = state["relato_inicial"]
    erros = list(state.get("erros", []))
    rag_interno = []
    if retriever is not None:
        try:
            rag_interno = retriever.retrieve_interno(query, k=6)
        except Exception as exc:  # noqa: BLE001
            erros.append(f"Retrieval falhou: {exc}")
            rag_interno = []
    return {
        **state,
        "rag_pmc_chunks": [],
        "rag_interno_chunks": rag_interno,
        "erros": erros,
    }


def node_sintese(state, llm_client=None):
    from src.agents.sintese import sintetizar

    erros = list(state.get("erros", []))
    try:
        sintese_result = sintetizar(
            state["relato_inicial"],
            state.get("rag_pmc_chunks", []),
            state.get("rag_interno_chunks", []),
            historico_paciente=state.get("historico_paciente"),
            llm_client=llm_client,
        )
    except Exception as exc:  # noqa: BLE001
        erros.append(f"Síntese falhou: {exc}")
        sintese_result = dict(SINTESE_FALLBACK)

    return {**state, "sintese": sintese_result, "erros": erros}


def node_validacao(state, llm_client=None):
    from src.agents.validacao import validar

    erros = list(state.get("erros", []))
    try:
        validated = validar(state["sintese"], state["triagem"], llm_client)
    except Exception as exc:  # noqa: BLE001
        erros.append(f"Validação falhou: {exc}")
        validated = state.get("sintese") or dict(SINTESE_FALLBACK)

    return {**state, "validacao": validated, "erros": erros}


def node_hitl(state):
    """Pausa o grafo aguardando a decisão do médico (aprovar/editar/rejeitar).

    Usa `interrupt()` do LangGraph: a execução para aqui de verdade até que
    a API retome com `Command(resume={"decisao": ..., "texto_editado": ...})`
    (ver POST /api/consulta/{session_id}/decisao em src/api/app.py). Sem
    resume, o nó `gerar_docs` nunca roda — nenhum documento é emitido sem
    essa decisão humana.
    """
    from langgraph.types import interrupt

    decisao_info = interrupt({
        "tipo": "aprovacao_medica",
        "triagem": state.get("triagem"),
        "sintese": state.get("validacao") or state.get("sintese"),
    }) or {}

    return {
        "medico_decisao": decisao_info.get("decisao"),
        "texto_editado": decisao_info.get("texto_editado") or state.get("texto_editado"),
    }


def node_gerar_docs(state, doc_generator):
    if state.get("medico_decisao") == "rejeitado":
        return state

    erros = list(state.get("erros", []))
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

    try:
        doc_path = doc_generator.gerar_prontuario(dados)
        with open(doc_path, "rb") as f:
            doc_hash = hashlib.sha256(f.read()).hexdigest()
    except Exception as exc:  # noqa: BLE001
        erros.append(f"Geração de PDF falhou: {exc}")
        return {**state, "erros": erros}

    return {
        **state,
        "documento_final": doc_path,
        "hash_documento": doc_hash,
        "erros": erros,
    }
