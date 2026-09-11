"""
Agente 1: TRIAGEM — classifica urgência de relatos clínicos.
Usa LLM real (BioMistral fine-tuned) se disponível, senão mock.
"""

import json
import re
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.llm.client import get_llm


TRIAGEM_SYSTEM_PROMPT = """Você é um assistente de TRIAGEM CLÍNICA de um hospital.

TAREFA: Classificar a urgência de um relato clínico.

CATEGORIAS (escolha EXATAMENTE uma):
- EMERGENCIA: risco iminente de vida (sepse, IAM, AVC, anafilaxia, parada cardíaca)
- URGENTE: necessita atenção em horas (dor intensa, sangramento moderado, febre alta persistente)
- ROTINA: pode aguardar consulta agendada (sintomas leves, crônicos estáveis)

RESPONDA EM JSON ESTRITO:
{
  "categoria": "EMERGENCIA|URGENTE|ROTINA",
  "justificativa": "<máx 200 caracteres>",
  "red_flags": ["<sinal de alerta 1>", "<sinal de alerta 2>"],
  "confianca": "alta|media|baixa"
}

⚠️ Em caso de dúvida entre URGENTE e EMERGENCIA, escolha EMERGENCIA.
⚠️ NÃO prescreva nada. NÃO dê diagnóstico. Apenas CLASSIFIQUE a urgência."""


def triar(relato: str, llm_client: Optional[object] = None) -> dict:
    """Classifica urgência usando LLM real ou fallback.

    Se `llm_client` for um chat model do langchain-core (usado quando o grafo
    LangGraph é executado via `criar_workflow`), a chamada é feita pela
    interface do langchain-core. Caso contrário, usa o LLMClient direto
    (get_llm()) — mesmo comportamento de sempre.
    """
    if isinstance(llm_client, BaseChatModel):
        resposta = llm_client.invoke([
            SystemMessage(content=TRIAGEM_SYSTEM_PROMPT),
            HumanMessage(content=f"Relato: {relato}"),
        ])
        text = resposta.content
    else:
        llm = llm_client or get_llm()
        messages = [
            {"role": "system", "content": TRIAGEM_SYSTEM_PROMPT},
            {"role": "user", "content": f"Relato: {relato}"},
        ]
        text = llm.invoke(messages)

    # Parse JSON (try/except com fallback)
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            result = json.loads(match.group(0))
            # Validar campos
            if "categoria" in result:
                return result
    except (json.JSONDecodeError, AttributeError):
        pass

    # Fallback seguro
    return {
        "categoria": "URGENTE",
        "justificativa": "Falha no parsing — assumindo URGENTE por segurança",
        "red_flags": [],
        "confianca": "baixa",
    }