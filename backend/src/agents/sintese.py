"""
Agente 2: SÍNTESE — gera hipóteses diagnósticas + condutas.
Usa LLM real (BioMistral fine-tuned) se disponível, senão mock.
"""

import json
import re
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.llm.client import get_llm


SINTESE_SYSTEM_PROMPT = """Você é um assistente de SÍNTESE CLÍNICA de um hospital.

TAREFA: Com base no relato do paciente + literatura médica + protocolos internos,
sugerir:
1. HIPÓTESES DIAGNÓSTICAS (com CID-10 quando possível)
2. EXAMES COMPLEMENTARES
3. MEDICAÇÕES POTENCIAIS (sempre com aviso de validação)

REGRAS:
- SEMPRE cite a FONTE: [Fonte: PMC-XXXX] ou [Fonte: SOP-XXX]
- Cada hipótese DEVE ter nível de confiança (alta, média, baixa)
- Medicações são SUGESTÕES — NUNCA prescrições definitivas
- Use APENAS o contexto fornecido

RESPONDA EM JSON ESTRITO:
{
  "hipoteses": [{"cid10": "X.XX", "nome": "...", "probabilidade": "alta|media|baixa", "justificativa": "...", "fonte": "..."}],
  "exames_sugeridos": [{"nome": "...", "justificativa": "...", "fonte": "..."}],
  "medicacoes_sugeridas": [{"nome": "...", "dose": "...", "frequencia": "...", "NOTA": "VALIDAÇÃO OBRIGATÓRIA"}],
  "observacoes": "..."
}"""


def _formatar_historico(historico_paciente: Optional[dict]) -> str:
    if not historico_paciente:
        return "(sem histórico prévio disponível)"

    partes = []
    condicoes = historico_paciente.get("condicoes_cronicas") or []
    alergias = historico_paciente.get("alergias") or []
    if condicoes:
        partes.append(f"Condições crônicas: {', '.join(condicoes)}")
    if alergias:
        partes.append(f"Alergias: {', '.join(alergias)}")

    for consulta in (historico_paciente.get("historico") or [])[:3]:
        partes.append(
            f"[{consulta.get('data', '?')}] {consulta.get('motivo', '?')} -> "
            f"{consulta.get('diagnostico', '?')} "
            f"(medicações: {', '.join(consulta.get('medicacoes', [])) or 'nenhuma'})"
        )

    return "\n".join(partes) if partes else "(sem histórico prévio disponível)"


def sintetizar(
    relato: str,
    rag_pmc: list,
    rag_interno: list,
    historico_paciente: Optional[dict] = None,
    llm_client: Optional[object] = None,
) -> dict:
    """Gera síntese usando LLM real ou fallback.

    `historico_paciente` (opcional) é o prontuário estruturado do paciente,
    consultado via tool do LangChain (src/graph/tools.py), e entra no prompt
    como contexto adicional. `llm_client`: ver docstring de `triar()`.
    """

    # Formatar contexto RAG
    contexto_pmc = "\n".join(
        f"[Fonte: {c.get('source', 'PMC')}] {c.get('content', '')[:300]}"
        for c in rag_pmc[:3]
    ) or "(sem resultados relevantes)"

    contexto_interno = "\n".join(
        f"[Fonte: {c.get('source', 'SOP')}] {c.get('content', '')[:300]}"
        for c in rag_interno[:3]
    ) or "(sem protocolos específicos)"

    contexto_paciente = _formatar_historico(historico_paciente)

    user_content = f"""
RELATO: {relato}

=== HISTÓRICO DO PACIENTE ===
{contexto_paciente}

=== LITERATURA (PMC) ===
{contexto_pmc}

=== PROTOCOLOS INTERNOS ===
{contexto_interno}

Resposta JSON:"""

    if isinstance(llm_client, BaseChatModel):
        resposta = llm_client.invoke([
            SystemMessage(content=SINTESE_SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ])
        text = resposta.content
    else:
        llm = llm_client or get_llm()
        messages = [
            {"role": "system", "content": SINTESE_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
        text = llm.invoke(messages)

    # Parse JSON
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            result = json.loads(match.group(0))
            if "hipoteses" in result or "observacoes" in result:
                return result
    except (json.JSONDecodeError, AttributeError):
        pass

    # Fallback
    return {
        "hipoteses": [],
        "exames_sugeridos": [],
        "medicacoes_sugeridas": [],
        "observacoes": "Falha no parsing.",
        "_erro": True,
    }