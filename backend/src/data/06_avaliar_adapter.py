"""
Avalia um adapter medindo a perplexidade em um conjunto que ele não viu.

Perplexidade é o quanto o modelo se "surpreende" com a resposta correta:
quanto menor, melhor. É a mesma métrica usada no relatório técnico
(4,31 no modelo base contra 2,18 no fine-tunado com MedQuAD).

Uso:
    python src/data/06_avaliar_adapter.py <adapter> <arquivo.jsonl>

Requer GPU. O modelo base é carregado em 4 bits.
"""

import json
import math
import os
import sys
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

BASE = os.getenv("LLM_BASE_MODEL", "BioMistral/BioMistral-7B")
MAX_LEN = int(os.getenv("MAX_LEN", "1024"))

ALPACA = (
    "Below is an instruction that describes a task, paired with an input that "
    "provides further context. Write a response that appropriately completes "
    "the request.\n\n"
    "### Instruction:\n{}\n\n"
    "### Input:\n{}\n\n"
    "### Response:\n{}"
)


def perplexidade(adapter: str, arquivo: Path) -> tuple[float, int]:
    tokenizer = AutoTokenizer.from_pretrained(BASE)
    tokenizer.pad_token = tokenizer.eos_token

    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    modelo = AutoModelForCausalLM.from_pretrained(
        BASE, quantization_config=quant, device_map="auto", torch_dtype=torch.bfloat16
    )
    if adapter and adapter != "base":
        modelo = PeftModel.from_pretrained(modelo, adapter)
    modelo.eval()

    perdas = []
    with arquivo.open(encoding="utf-8") as f:
        for linha in f:
            obj = json.loads(linha)
            texto = ALPACA.format(obj["instruction"], obj.get("input", ""), obj["output"])
            entrada = tokenizer(
                texto, return_tensors="pt", truncation=True, max_length=MAX_LEN
            ).to(modelo.device)
            with torch.no_grad():
                saida = modelo(**entrada, labels=entrada["input_ids"])
            perdas.append(saida.loss.item())

    media = sum(perdas) / len(perdas)
    return math.exp(media), len(perdas)


def main() -> None:
    assert torch.cuda.is_available(), "Sem GPU: este script precisa de uma placa CUDA."
    adapter = sys.argv[1] if len(sys.argv) > 1 else "base"
    arquivo = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/processed/dados_internos_validacao.jsonl")

    ppl, n = perplexidade(adapter, arquivo)
    print(f"adapter={adapter} | arquivo={arquivo.name} | exemplos={n} | perplexidade={ppl:.2f}")


if __name__ == "__main__":
    main()
