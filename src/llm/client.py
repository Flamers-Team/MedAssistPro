"""
LLM client: carrega o modelo BioMistral fine-tuned (se existir) ou levanta erro claro.

SEM MOCK. SEM FALLBACK. Se a LLM não tá disponível, levanta RuntimeError com mensagem clara.
Por quê: dados falsos podem causar decisões clínicas erradas. Melhor falhar honestamente.

Uso:
    from src.llm.client import LLMClient, get_llm
    llm = get_llm()  # singleton global
    response = llm.invoke([
        {"role": "system", "content": "Você é médico."},
        {"role": "user", "content": "Paciente com..."}
    ])

Erros comuns:
- RuntimeError: "LLM não foi carregada. Rode o fine-tuning primeiro."
- RuntimeError: "Falha ao carregar modelo: <detalhes>"
- RuntimeError: "Erro na inferência: <detalhes>"

Autor: Michelle Nogueira (Tech Challenge FIAP - Fase 3)
"""

from pathlib import Path
from typing import Optional
import os


# Paths padrão
DEFAULT_LORA_PATH = Path("biomistral-medquad-lora")
DEFAULT_BASE_MODEL = "BioMistral/BioMistral-7B"


class LLMNotAvailableError(RuntimeError):
    """Levantada quando a LLM não pôde ser carregada ou invocada."""
    pass


class LLMClient:
    """Wrapper que carrega BioMistral-7B + LoRA adapters."""

    def __init__(
        self,
        base_model: str = DEFAULT_BASE_MODEL,
        lora_path: Path = DEFAULT_LORA_PATH,
        device: str = "auto",
        load_in_4bit: bool = True,
    ):
        self.base_model = base_model
        self.lora_path = Path(lora_path)
        self.device = device
        self.load_in_4bit = load_in_4bit
        self.model = None
        self.tokenizer = None
        self.use_mock = True  # até conseguir carregar

        # Tentar carregar modelo real
        if not self.lora_path.exists():
            raise LLMNotAvailableError(
                f"Modelo LoRA não encontrado em {self.lora_path}. "
                f"Você rodou o fine-tuning? O caminho está correto? "
                f"Esperado: {self.lora_path.absolute()}"
            )

        try:
            self._carregar_modelo_real()
            self.use_mock = False
        except Exception as e:
            raise LLMNotAvailableError(
                f"Falha ao carregar modelo de {self.lora_path}: {e}"
            )

    def _carregar_modelo_real(self):
        """Carrega BioMistral + LoRA do disco."""
        try:
            from unsloth import FastLanguageModel
            import torch
        except ImportError:
            raise ImportError(
                "Instale: pip install unsloth transformers peft bitsandbytes"
            )

        print(f"🔄 Carregando {self.base_model} + LoRA de {self.lora_path}...")
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name=str(self.lora_path),
            max_seq_length=4096,
            dtype=None,
            load_in_4bit=self.load_in_4bit,
        )
        FastLanguageModel.for_inference(self.model)
        print("✅ Modelo carregado!")

    def invoke(self, messages: list) -> str:
        """Chama o LLM com uma lista de mensagens (formato OpenAI).

        Args:
            messages: lista de dicts com "role" e "content"

        Returns:
            Resposta gerada pelo modelo (string)

        Raises:
            LLMNotAvailableError: se LLM não foi carregada
            RuntimeError: se inferência falhar
        """
        if not messages:
            raise ValueError("messages não pode ser vazio")

        if self.use_mock or self.model is None:
            raise LLMNotAvailableError(
                "LLM não foi carregada. Rode o fine-tuning primeiro "
                "e verifique se o modelo está em " + str(self.lora_path)
            )

        try:
            # Formatar prompt
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                repetition_penalty=1.3,
            )
            response = self.tokenizer.decode(
                outputs[0][inputs.input_ids.shape[1]:],
                skip_special_tokens=True,
            )
            return response.strip()
        except Exception as e:
            # Erro CLARO - sem fallback, sem dado falso
            raise RuntimeError(
                f"Erro na inferência do LLM: {e}. "
                f"Verifique: GPU disponível? Memória suficiente? "
                f"Modelo carregado corretamente?"
            )


# ============================================================
# SINGLETON GLOBAL (pra evitar carregar modelo várias vezes)
# ============================================================
_llm_instance: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    """Retorna instância singleton do LLM.

    Raises:
        LLMNotAvailableError: se modelo não tá carregado
    """
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMClient()
    return _llm_instance


# ============================================================
# TESTE
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 TESTANDO LLM CLIENT (sem mock)")
    print("=" * 60)

    try:
        llm = get_llm()
    except LLMNotAvailableError as e:
        print(f"\n❌ {type(e).__name__}: {e}")
        print("\n💡 Para resolver:")
        print("   1. Rode o fine-tuning (notebooks/02_finetuning.ipynb)")
        print("   2. Salve o modelo em biomistral-medquad-lora/")
        print("   3. Rode este script novamente")
        sys.exit(1)

    # Testa inferência real
    print("\n--- TESTE DE INFERÊNCIA ---")
    resp = llm.invoke([
        {"role": "system", "content": "Você é um assistente médico."},
        {"role": "user", "content": "What are the symptoms of diabetes?"},
    ])
    print(f"\n✅ Resposta da LLM:")
    print(resp[:500])
