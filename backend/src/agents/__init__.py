"""
ETAPA 3: Estrutura do LangGraph com 3 agentes.

Componentes:
- src/agents/triagem.py      - Agente 1: classifica urgência
- src/agents/sintese.py      - Agente 2: hipóteses + condutas
- src/agents/validacao.py    - Agente 3: aplica guardrails
- src/graph/state.py         - Estado compartilhado
- src/graph/nodes.py         - 6 nós do grafo
- src/graph/workflow.py      - StateGraph completo

Autor: Michelle Nogueira (Tech Challenge FIAP - Fase 3)
"""

from typing import Literal, Optional, TypedDict


class ConversationState(TypedDict):
    relato_inicial: str
    dados_paciente: Optional[dict]
    triagem: Optional[dict]
    sintese: Optional[dict]
    validacao: Optional[dict]
    rag_pmc_chunks: list[dict]
    rag_interno_chunks: list[dict]
    medico_decisao: Optional[Literal["aprovado", "editado", "rejeitado"]]
    texto_editado: Optional[str]
    documento_final: Optional[str]
    hash_documento: Optional[str]
    session_id: str
    timestamp_inicio: str
    erros: list[str]
