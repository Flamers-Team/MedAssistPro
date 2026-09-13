"""
Continua o fine-tuning do adapter a partir dos dados internos do hospital.

Parte do adapter já publicado (treinado no MedQuAD) e treina por cima com o
dataset interno, em vez de treinar do zero: é mais rápido e preserva o que o
modelo já aprendeu.

Uso (na máquina com GPU):
    python src/data/05_treinar_adapter.py [arquivo.jsonl] [pasta_de_saida]

Requer GPU. O modelo base é carregado em 4 bits (QLoRA).
"""

import json
import os
import sys
import time
from pathlib import Path

import torch
from peft import PeftModel, prepare_model_for_kbit_training
from torch.utils.data import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

BASE = os.getenv("LLM_BASE_MODEL", "BioMistral/BioMistral-7B")
ADAPTER = os.getenv("LLM_MODEL", "michelleAnogueira/biomistral-medquad-lora")
MAX_LEN = int(os.getenv("MAX_LEN", "1024"))
EPOCAS = float(os.getenv("EPOCAS", "3"))
LR = float(os.getenv("LR", "1e-4"))

ARQUIVO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/processed/dados_internos_anonimizado.jsonl")
SAIDA = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/opt/medassist/adapter-v2")

# Mesmo template do fine-tuning original (notebooks/02_finetuning.ipynb).
ALPACA = (
    "Below is an instruction that describes a task, paired with an input that "
    "provides further context. Write a response that appropriately completes "
    "the request.\n\n"
    "### Instruction:\n{}\n\n"
    "### Input:\n{}\n\n"
    "### Response:\n{}"
)


class DatasetInterno(Dataset):
    def __init__(self, caminho: Path, tokenizer, max_len: int):
        self.exemplos = []
        with caminho.open(encoding="utf-8") as f:
            for linha in f:
                obj = json.loads(linha)
                texto = ALPACA.format(
                    obj["instruction"], obj.get("input", ""), obj["output"]
                ) + tokenizer.eos_token
                self.exemplos.append(
                    tokenizer(texto, truncation=True, max_length=max_len)
                )

    def __len__(self):
        return len(self.exemplos)

    def __getitem__(self, i):
        return self.exemplos[i]


def main() -> None:
    assert torch.cuda.is_available(), "Sem GPU: este script precisa de uma placa CUDA."
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Dataset: {ARQUIVO}")

    tokenizer = AutoTokenizer.from_pretrained(BASE)
    tokenizer.pad_token = tokenizer.eos_token

    dados = DatasetInterno(ARQUIVO, tokenizer, MAX_LEN)
    print(f"Exemplos: {len(dados)}")

    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    t0 = time.time()
    modelo = AutoModelForCausalLM.from_pretrained(
        BASE, quantization_config=quant, device_map="auto", torch_dtype=torch.bfloat16
    )
    modelo = prepare_model_for_kbit_training(modelo)
    modelo = PeftModel.from_pretrained(modelo, ADAPTER, is_trainable=True)
    modelo.config.use_cache = False
    treinaveis = sum(p.numel() for p in modelo.parameters() if p.requires_grad)
    print(f"Carga: {time.time()-t0:.0f}s | parâmetros treináveis: {treinaveis/1e6:.1f}M")

    args = TrainingArguments(
        output_dir=str(SAIDA / "checkpoints"),
        num_train_epochs=EPOCAS,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=LR,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        logging_steps=5,
        save_strategy="no",
        bf16=True,
        optim="adamw_torch",
        report_to=[],
    )

    trainer = Trainer(
        model=modelo,
        args=args,
        train_dataset=dados,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )

    t1 = time.time()
    resultado = trainer.train()
    print(f"Treino: {(time.time()-t1)/60:.1f} min | loss final: {resultado.training_loss:.4f}")

    modelo.save_pretrained(str(SAIDA))
    tokenizer.save_pretrained(str(SAIDA))
    print(f"Adapter salvo em: {SAIDA}")


if __name__ == "__main__":
    main()
