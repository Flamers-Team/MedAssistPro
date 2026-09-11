from src.graph.nodes import node_contexto_paciente, node_triagem, node_sintese
from src.graph.tools import consultar_prontuario
from src.llm.langchain_client import BioMistralChatModel, get_langchain_llm


def test_consultar_prontuario_tool_retorna_dados_do_paciente():
    resultado = consultar_prontuario.invoke({"paciente_id": "PAC-0002"})
    assert resultado["paciente_id"] == "PAC-0002"
    assert "condicoes_cronicas" in resultado


def test_consultar_prontuario_tool_paciente_inexistente_retorna_vazio():
    resultado = consultar_prontuario.invoke({"paciente_id": "PAC-NAO-EXISTE"})
    assert resultado == {}


def test_node_contexto_paciente_preenche_historico_quando_ha_id():
    state = {"relato_inicial": "x", "paciente_id": "PAC-0002", "erros": []}
    novo_state = node_contexto_paciente(state)
    assert novo_state["historico_paciente"]["paciente_id"] == "PAC-0002"


def test_node_contexto_paciente_sem_id_nao_falha():
    state = {"relato_inicial": "x", "paciente_id": None, "erros": []}
    novo_state = node_contexto_paciente(state)
    assert novo_state["historico_paciente"] == {}
    assert novo_state["erros"] == []


def test_node_triagem_degrada_para_fallback_quando_llm_falha(monkeypatch):
    def quebra(*args, **kwargs):
        raise RuntimeError("LLM indisponivel")

    monkeypatch.setattr("src.agents.triagem.triar", quebra)

    state = {"relato_inicial": "Febre", "erros": []}
    novo_state = node_triagem(state)

    assert novo_state["triagem"]["categoria"] == "ROTINA"
    assert len(novo_state["erros"]) == 1


def test_node_sintese_degrada_para_fallback_quando_agente_falha(monkeypatch):
    def quebra(*args, **kwargs):
        raise RuntimeError("parsing falhou")

    monkeypatch.setattr("src.agents.sintese.sintetizar", quebra)

    state = {
        "relato_inicial": "Febre",
        "rag_pmc_chunks": [],
        "rag_interno_chunks": [],
        "historico_paciente": None,
        "erros": [],
    }
    novo_state = node_sintese(state)

    assert novo_state["sintese"]["hipoteses"] == []
    assert len(novo_state["erros"]) == 1


def test_langchain_chat_model_responde_via_invoke():
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_langchain_llm()
    assert isinstance(llm, BioMistralChatModel)

    resposta = llm.invoke([
        SystemMessage(content="Você é um assistente de TRIAGEM CLÍNICA."),
        HumanMessage(content="Relato: paciente com febre."),
    ])
    assert isinstance(resposta.content, str)
    assert resposta.content
