"""
Assistente Médico com Fine-Tuning + Tradução PT-BR <-> EN
=========================================================

Pipeline:
  Pergunta PT-BR
      ↓
  [MarianMT PT → EN]
      ↓
  [BioMistral Fine-Tuned via transformers + peft] (GPU com 4-bit ou CPU)
      ↓
  [MarianMT EN → PT]
      ↓
  Resposta PT-BR (terminologia médica brasileira)

Reaproveita os componentes já usados pela API (src/llm/tradutor.py e
src/llm/client.py) em vez de carregar o modelo de novo — mesma detecção
de GPU/CPU, mesmo LORA/base model, mesmo modo mock (LLM_MOCK=1).

Modelos:
  - LLM: biomistral-medquad-lora (fine-tuning) ou BioMistral/BioMistral-7B base
  - Tradutor EN→PT: Helsinki-NLP/opus-mt-tc-big-en-pt
  - Tradutor PT→EN: Helsinki-NLP/opus-mt-tc-big-pt-en

Uso:
  python assistente_traduzido.py
  ou
  from src.llm.assistente_traduzido import AssistenteTraduzido
  bot = AssistenteTraduzido()
  print(bot.perguntar("O que é diabetes?"))
"""

from __future__ import annotations

import time
from typing import Optional

from src.llm.client import LLMClient, get_llm
from src.llm.tradutor import get_tradutor


class AssistenteTraduzido:
    """Assistente médico com tradução automática PT-BR <-> EN."""

    def __init__(self, modelo_path: Optional[str] = None, **_ignored):
        self.tradutor = get_tradutor()
        self.llm: LLMClient = LLMClient(lora_path=modelo_path) if modelo_path else get_llm()

    def perguntar(self, pergunta_pt: str, topico_en: str = "", verbose: bool = False) -> str:
        """
        Faz pergunta em PT-BR, retorna resposta em PT-BR.

        Args:
            pergunta_pt: Pergunta em português brasileiro
            topico_en: Tópico em inglês (opcional, para RAG)
            verbose: Se True, mostra os passos intermediários

        Returns:
            Resposta em português brasileiro
        """
        t0 = time.time()

        if verbose:
            print(f"  Pergunta original: {pergunta_pt}")
        pergunta_en = self.tradutor.pt_para_en(pergunta_pt)
        if verbose:
            print(f"  Traducao EN: {pergunta_en}")

        mensagens = [{"role": "system", "content": "You are a medical assistant."}]
        if topico_en:
            mensagens.append({"role": "system", "content": f"Context / Topic: {topico_en}"})
        mensagens.append({"role": "user", "content": pergunta_en})

        resposta_en = self.llm.invoke(mensagens)
        if verbose:
            print(f"  LLM EN: {resposta_en[:200]}...")

        resposta_pt = self.tradutor.en_para_pt(resposta_en)
        if verbose:
            print(f"  Traducao PT: {resposta_pt[:200]}...")
            print(f"  Tempo total: {time.time() - t0:.1f}s")

        return resposta_pt

    def conversar(self):
        """Modo conversacional interativo."""
        print("=" * 70)
        print("ASSISTENTE MEDICO COM TRADUCAO AUTOMATICA")
        print("=" * 70)
        print("Faça perguntas em português brasileiro.")
        print("Digite 'sair' ou 'exit' para encerrar.")
        print("=" * 70)

        while True:
            try:
                pergunta = input("\nPergunta: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nAte logo!")
                break

            if not pergunta:
                continue
            if pergunta.lower() in ("sair", "exit", "quit"):
                print("Ate logo!")
                break

            resposta = self.perguntar(pergunta, verbose=True)
            print(f"\nResposta:\n{resposta}")
            print("-" * 70)


def main():
    """Demonstração rápida."""
    bot = AssistenteTraduzido(modelo_path="biomistral-medquad-lora")

    perguntas_teste = [
        "O que é diabetes?",
        "Quais são os sintomas de pneumonia?",
        "Como funciona a vacina de mRNA?",
        "O que causa AVC?",
        "Quais são os tratamentos para hipertensão?",
    ]

    print("\n" + "=" * 70)
    print("TESTES RAPIDOS")
    print("=" * 70)

    for pergunta in perguntas_teste:
        print(f"\n{pergunta}")
        resposta = bot.perguntar(pergunta, verbose=False)
        print(f"{resposta[:300]}...")
        print("-" * 70)

    print("\nEntrando em modo conversacional...")
    bot.conversar()


if __name__ == "__main__":
    main()
