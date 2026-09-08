"""
LLM client — carrega o adapter LoRA do fine-tuning (BioMistral + MedQuAD)
via transformers + peft (SEM unsloth, para máxima compatibilidade no Colab).

Resolução do modelo (nesta ordem):
  1. argumento `lora_path`
  2. env var LLM_MODEL
  3. default "michelleAnogueira/biomistral-medquad-lora"
O valor pode ser um repo do HuggingFace Hub OU um diretório local.

Modo mock: env var LLM_MOCK=1  → respostas sintéticas (permite testar a
pipeline/UI sem GPU). Sem isso, falha de forma explícita (LLMNotAvailableError).

Uso:
    from src.llm.client import get_llm
    llm = get_llm()
    txt = llm.invoke([
        {"role": "system", "content": "Você é um assistente de triagem."},
        {"role": "user",   "content": "Paciente com dor torácica há 2h..."},
    ])
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional


DEFAULT_LLM_MODEL = os.getenv("LLM_MODEL", "michelleAnogueira/biomistral-medquad-lora")
DEFAULT_BASE_MODEL = os.getenv("LLM_BASE_MODEL", "BioMistral/BioMistral-7B")

# Mantidos por retrocompatibilidade com imports antigos
DEFAULT_LORA_PATH = DEFAULT_LLM_MODEL

# Template Alpaca — o MESMO do fine-tuning (notebooks/02_finetuning.ipynb, Seção 6.1)
ALPACA_PROMPT = (
    "Below is an instruction that describes a task, paired with an input that "
    "provides further context. Write a response that appropriately completes "
    "the request.\n\n"
    "### Instruction:\n{instruction}\n\n"
    "### Input:\n{input}\n\n"
    "### Response:\n"
)


class LLMNotAvailableError(RuntimeError):
    """Levantada quando a LLM não pôde ser carregada ou invocada."""


def _messages_to_alpaca(messages: list) -> str:
    """Converte mensagens estilo OpenAI para o prompt Alpaca do fine-tuning."""
    system = "\n\n".join(m["content"] for m in messages if m.get("role") == "system")
    user = "\n\n".join(m["content"] for m in messages if m.get("role") == "user")
    instruction = f"{system}\n\n{user}".strip() if system else user.strip()
    return ALPACA_PROMPT.format(instruction=instruction, input="")


class LLMClient:
    """Carrega BioMistral-7B (4-bit) + adapter LoRA e faz inferência."""

    def __init__(
        self,
        lora_path: Optional[str] = None,
        base_model: str = DEFAULT_BASE_MODEL,
        load_in_4bit: bool = True,
        mock: Optional[bool] = None,
        **_ignored,
    ):
        self.lora_ref = str(lora_path or DEFAULT_LLM_MODEL)
        self.base_model = base_model
        self.load_in_4bit = load_in_4bit
        self.model = None
        self.tokenizer = None

        if mock is None:
            mock = os.getenv("LLM_MOCK", "").lower() in ("1", "true", "yes", "on")
        self.use_mock = bool(mock)

        if self.use_mock:
            print("⚠️  LLMClient em MODO MOCK — respostas sintéticas (LLM_MOCK=1).")
            return

        try:
            self._carregar_modelo_real()
        except Exception as e:  # noqa: BLE001
            raise LLMNotAvailableError(
                f"Falha ao carregar o modelo '{self.lora_ref}': {e}\n"
                "  • rode em runtime com GPU;\n"
                "  • se o repo do adapter for privado, faça huggingface_hub.login();\n"
                "  • para testar sem GPU/modelo, defina LLM_MOCK=1."
            ) from e

    # ------------------------------------------------------------------
    def _candidate_bases(self) -> list:
        """Descobre o(s) base model(s) candidatos a partir do adapter_config.json."""
        cands: list = []
        cfg = None
        local_cfg = Path(self.lora_ref) / "adapter_config.json"
        try:
            if local_cfg.exists():
                cfg = json.loads(local_cfg.read_text())
            else:
                from huggingface_hub import hf_hub_download

                cfg = json.loads(
                    Path(hf_hub_download(self.lora_ref, "adapter_config.json")).read_text()
                )
        except Exception:  # noqa: BLE001
            cfg = None

        if cfg and cfg.get("base_model_name_or_path"):
            cands.append(cfg["base_model_name_or_path"])
        if self.base_model not in cands:
            cands.append(self.base_model)
        return cands

    def _carregar_modelo_real(self):
        import torch
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
        )
        from peft import PeftModel

        has_cuda = torch.cuda.is_available()
        quant = None
        if self.load_in_4bit and has_cuda:
            quant = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
            )

        self.tokenizer = AutoTokenizer.from_pretrained(self.lora_ref)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        last_err = None
        for base in self._candidate_bases():
            pre_quant = any(t in base.lower() for t in ("4bit", "bnb", "gptq", "awq"))
            try:
                print(f"🔄 Carregando base '{base}' + LoRA '{self.lora_ref}'...")
                model = AutoModelForCausalLM.from_pretrained(
                    base,
                    quantization_config=None if pre_quant else quant,
                    device_map="auto" if has_cuda else None,
                    torch_dtype=torch.bfloat16 if has_cuda else torch.float32,
                )
                self.model = PeftModel.from_pretrained(model, self.lora_ref)
                self.model.eval()
                print("✅ Modelo carregado (transformers + peft).")
                return
            except Exception as e:  # noqa: BLE001
                print(f"   ✗ falhou com base '{base}': {e}")
                last_err = e
        raise last_err or RuntimeError("Nenhum base model utilizável.")

    # ------------------------------------------------------------------
    def invoke(self, messages: list) -> str:
        """Chama o LLM com uma lista de mensagens (formato OpenAI). Retorna string."""
        if not messages:
            raise ValueError("messages não pode ser vazio")
        if self.use_mock:
            return self._mock_response(messages)
        if self.model is None or self.tokenizer is None:
            raise LLMNotAvailableError("Modelo não carregado.")

        import torch

        prompt = _messages_to_alpaca(messages)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        try:
            with torch.no_grad():
                out = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    repetition_penalty=1.2,
                    pad_token_id=self.tokenizer.pad_token_id,
                )
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"Erro na inferência do LLM: {e}") from e

        gen = out[0][inputs["input_ids"].shape[1]:]
        return self.tokenizer.decode(gen, skip_special_tokens=True).strip()

    # ------------------------------------------------------------------
    @staticmethod
    def _mock_response(messages: list) -> str:
        blob = " ".join(m.get("content", "") for m in messages).upper()
        if "TRIAGEM" in blob:
            return json.dumps({
                "categoria": "URGENTE",
                "justificativa": "[MOCK] resposta sintética (LLM_MOCK=1).",
                "red_flags": ["mock"],
                "confianca": "baixa",
            }, ensure_ascii=False)
        if "SÍNTESE" in blob or "SINTESE" in blob:
            return json.dumps({
                "hipoteses": [{
                    "cid10": "R69", "nome": "[MOCK] hipótese sintética",
                    "probabilidade": "baixa", "justificativa": "mock", "fonte": "MOCK",
                }],
                "exames_sugeridos": [
                    {"nome": "[MOCK] Hemograma completo", "justificativa": "mock", "fonte": "MOCK"}
                ],
                "medicacoes_sugeridas": [],
                "observacoes": "[MOCK] Ative a LLM real: GPU + LLM_MOCK=0.",
            }, ensure_ascii=False)
        return "[MOCK] Resposta sintética. Ative a LLM real (GPU + LLM_MOCK=0) para uso normal."


# ============================================================
# SINGLETON GLOBAL
# ============================================================
_llm_instance: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    """Retorna instância singleton do LLM."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMClient()
    return _llm_instance


# ============================================================
# TESTE
# ============================================================
if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("🤖 TESTANDO LLM CLIENT")
    print("=" * 60)
    try:
        _llm = get_llm()
    except LLMNotAvailableError as exc:
        print(f"\n❌ {exc}")
        sys.exit(1)

    print("\n--- TESTE DE INFERÊNCIA ---")
    resp = _llm.invoke([
        {"role": "system", "content": "You are a medical assistant."},
        {"role": "user", "content": "What are the symptoms of diabetes?"},
    ])
    print(resp[:500])
