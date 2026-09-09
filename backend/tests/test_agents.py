import json

from src.agents.sintese import sintetizar
from src.agents.triagem import triar
from src.agents.validacao import validar


class FakeLLM:
    def __init__(self, response):
        self.response = response

    def invoke(self, messages):
        return self.response


class SpyLLM:
    def __init__(self, response):
        self.response = response
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return self.response


# --- triagem ---------------------------------------------------------------

def test_triar_modo_mock_retorna_categoria_valida():
    resultado = triar("Paciente com febre e tosse ha 3 dias.")
    assert resultado["categoria"] in {"EMERGENCIA", "URGENTE", "ROTINA"}
    assert "justificativa" in resultado
    assert "red_flags" in resultado


def test_triar_fallback_quando_resposta_nao_e_json(monkeypatch):
    monkeypatch.setattr("src.agents.triagem.get_llm", lambda: FakeLLM("isso nao e um json valido"))
    resultado = triar("Relato qualquer")
    assert resultado["categoria"] == "URGENTE"
    assert "Falha no parsing" in resultado["justificativa"]


def test_triar_aceita_json_com_texto_ao_redor(monkeypatch):
    payload = {
        "categoria": "EMERGENCIA",
        "justificativa": "dor toracica",
        "red_flags": ["dor toracica"],
        "confianca": "alta",
    }
    monkeypatch.setattr(
        "src.agents.triagem.get_llm",
        lambda: FakeLLM(f"Aqui esta a resposta: {json.dumps(payload)} obrigado"),
    )
    resultado = triar("Dor no peito ha 2 horas")
    assert resultado == payload


# --- sintese -----------------------------------------------------------

def test_sintetizar_modo_mock_retorna_estrutura_esperada():
    resultado = sintetizar("Paciente com febre", rag_pmc=[], rag_interno=[])
    assert "hipoteses" in resultado
    assert "exames_sugeridos" in resultado
    assert "medicacoes_sugeridas" in resultado


def test_sintetizar_fallback_quando_resposta_invalida(monkeypatch):
    monkeypatch.setattr("src.agents.sintese.get_llm", lambda: FakeLLM("resposta sem json"))
    resultado = sintetizar("Relato", rag_pmc=[], rag_interno=[])
    assert resultado["_erro"] is True
    assert resultado["hipoteses"] == []


def test_sintetizar_inclui_contexto_rag_no_prompt(monkeypatch):
    spy = SpyLLM(json.dumps({
        "hipoteses": [], "exames_sugeridos": [], "medicacoes_sugeridas": [], "observacoes": "ok",
    }))
    monkeypatch.setattr("src.agents.sintese.get_llm", lambda: spy)

    rag_interno = [{"source": "chatbulario", "content": "Paracetamol 750mg de 6 em 6 horas"}]
    sintetizar("Dor de cabeca", rag_pmc=[], rag_interno=rag_interno)

    user_msg = spy.messages[1]["content"]
    assert "Paracetamol 750mg" in user_msg


# --- validacao (sem LLM, logica pura) ---------------------------------

def test_validar_adiciona_disclaimer_quando_ausente():
    resultado = validar({"hipoteses": [], "medicacoes_sugeridas": []}, {"categoria": "ROTINA"}, llm_client=None)
    assert "disclaimer" in resultado
    assert "Validação humana obrigatória" in resultado["disclaimer"]


def test_validar_preserva_disclaimer_existente():
    resultado = validar(
        {"disclaimer": "meu disclaimer customizado", "medicacoes_sugeridas": []}, {}, llm_client=None
    )
    assert resultado["disclaimer"] == "meu disclaimer customizado"


def test_validar_marca_todas_medicacoes_com_nota_obrigatoria():
    sintese = {
        "medicacoes_sugeridas": [
            {"nome": "Dipirona"},
            {"nome": "Ibuprofeno", "NOTA": "ja validado"},
        ]
    }
    resultado = validar(sintese, {}, llm_client=None)
    for med in resultado["medicacoes_sugeridas"]:
        assert "VALIDAÇÃO" in med["NOTA"]


def test_validar_anexa_triagem_ao_resultado():
    triagem = {"categoria": "URGENTE"}
    resultado = validar({}, triagem, llm_client=None)
    assert resultado["triagem"] == triagem
