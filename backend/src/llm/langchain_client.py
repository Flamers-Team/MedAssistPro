"""Encapsula o LLMClient (BioMistral + LoRA) como um chat model do langchain-core.

Permite que o LLM customizado seja usado dentro de pipelines/tools/grafos
do LangChain (via `.invoke(messages)` com mensagens do langchain-core),
em vez de ser chamado diretamente por fora do LangChain.

Uso:
    from langchain_core.messages import SystemMessage, HumanMessage
    from src.llm.langchain_client import get_langchain_llm

    llm = get_langchain_llm()
    resposta = llm.invoke([
        SystemMessage(content="Você é um assistente de triagem."),
        HumanMessage(content="Paciente com dor torácica há 2h..."),
    ])
    print(resposta.content)
"""

from __future__ import annotations

from typing import Any, List, Optional

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import PrivateAttr

from src.llm.client import LLMClient, get_llm

_ROLE_MAP = {"system": "system", "human": "user", "ai": "assistant"}


def _to_role_content(messages: List[BaseMessage]) -> List[dict]:
    """Converte mensagens do langchain-core pro formato aceito por LLMClient.invoke()."""
    return [{"role": _ROLE_MAP.get(m.type, "user"), "content": m.content} for m in messages]


class BioMistralChatModel(BaseChatModel):
    """Chat model do langchain-core que encapsula o LLMClient (BioMistral + LoRA).

    Não recarrega o modelo — delega para o LLMClient (singleton via get_llm()
    por padrão), então herda a mesma detecção de GPU/CPU e o mesmo modo mock.
    """

    _client: LLMClient = PrivateAttr()

    def __init__(self, client: Optional[LLMClient] = None, **kwargs: Any):
        super().__init__(**kwargs)
        self._client = client or get_llm()

    @property
    def _llm_type(self) -> str:
        return "biomistral-lora"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        texto = self._client.invoke(_to_role_content(messages))
        generation = ChatGeneration(message=AIMessage(content=texto))
        return ChatResult(generations=[generation])


_langchain_llm_instance: Optional[BioMistralChatModel] = None


def get_langchain_llm() -> BioMistralChatModel:
    """Retorna instância singleton do LLM encapsulado como chat model do langchain-core."""
    global _langchain_llm_instance
    if _langchain_llm_instance is None:
        _langchain_llm_instance = BioMistralChatModel()
    return _langchain_llm_instance
