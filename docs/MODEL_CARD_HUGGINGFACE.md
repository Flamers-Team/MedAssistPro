---
license: apache-2.0
base_model: BioMistral/BioMistral-7B
tags:
  - medical
  - healthcare
  - fine-tuned
  - lora
  - qlora
  - medquad
  - portuguese
  - biomistral
language:
  - en
  - pt
datasets:
  - MedQuAD
library_name: peft
pipeline_tag: text-generation
---

# 🏥 BioMistral-7B Fine-Tuned on MedQuAD

## Model Description

This is a **fine-tuned version of BioMistral-7B** on the [MedQuAD](https://github.com/abachaa/MedQuAD) dataset (16,325 medical Q&A pairs) using **QLoRA** (4-bit quantization + LoRA adapters).

The model was fine-tuned as part of the **Tech Challenge FIAP - Phase 3** (Final project for "AI for Developers" course) to build a medical assistant for Brazilian Portuguese healthcare professionals.

- **Developed by:** Flamers Team (FIAP Tech Challenge Phase 3)
- **Funded by:** Tech Challenge FIAP (academic project)
- **Model type:** Causal Language Model (decoder-only transformer)
- **Language(s):** English (training) + Portuguese (via translation layer)
- **License:** Apache 2.0 (inherited from BioMistral-7B)
- **Finetuned from:** [BioMistral/BioMistral-7B](https://huggingface.co/BioMistral/BioMistral-7B)

## Model Sources

- **Repository (GitHub):** https://github.com/Flamers-Team/MedAssistPro
- **Base model paper:** BioMistral: A Collection of Biomedical Large Language Models (https://arxiv.org/abs/2402.10373)

## Uses

### Direct Use

This model is designed to answer **medical questions in English** in a structured, clinical format inspired by NIH MedQuAD. It can be used for:

- Medical Q&A systems
- Clinical decision support (with human validation)
- Educational tools for healthcare students
- Research on medical LLM fine-tuning

### Downstream Use

This model is part of a larger medical assistant pipeline that includes:
- **RAG** (Retrieval-Augmented Generation) over 10k Brazilian drug labels (ChatBulário dataset)
- **Translation layer** (PT-BR ↔ EN using MarianMT)
- **3-agent LangGraph** (Triagem, Síntese, Validação)
- **HITL** (Human-in-the-Loop) mandatory validation
- **Audit logging** (SQLite)

### Out-of-Scope Use

⚠️ **This model is NOT a substitute for medical professionals.** It is an academic prototype and should NEVER be used for:
- Direct patient diagnosis without physician oversight
- Prescription generation without pharmacist/doctor validation
- Emergency medical decisions
- Production medical software

## Bias, Risks, and Limitations

- **Training data limitations:** MedQuAD is from NIH (USA), so it reflects American healthcare practices. Brazilian-specific protocols may differ.
- **Hallucination risk:** Like all LLMs, this model can generate plausible-sounding but factually incorrect medical information. Always validate with authoritative sources.
- **Language bias:** Trained primarily in English; PT-BR support requires additional translation layer.
- **No factual verification:** The model does not cite sources or verify claims against external databases (RAG is needed for that).
- **Knowledge cutoff:** BioMistral's pre-training data has a cutoff; new medical research may not be represented.

## Recommendations

Users (both direct and downstream) **must**:
1. Always have a qualified medical professional review outputs before clinical use
2. Never rely on this model as sole source of medical information
3. Combine with up-to-date RAG over authoritative medical databases
4. Implement strict HITL validation in any production pipeline
5. Monitor for hallucinations and bias in real-world deployments

## How to Get Started with the Model

### Installation

```bash
pip install torch transformers peft bitsandbytes accelerate
```

### Loading the model

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load base model
base_model = AutoModelForCausalLM.from_pretrained(
    "BioMistral/BioMistral-7B",
    load_in_4bit=True,  # QLoRA: 4-bit quantization
    device_map="auto",
)

# Load LoRA adapter (THIS REPO)
model = PeftModel.from_pretrained(base_model, "michelleAnogueira/biomistral-medquad-lora")

tokenizer = AutoTokenizer.from_pretrained("michelleAnogueira/biomistral-medquad-lora")
```

### Inference example

```python
# Alpaca-style prompt template
prompt = """Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
What are the symptoms of diabetes?

### Response:
"""

inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
outputs = model.generate(
    **inputs,
    max_new_tokens=512,
    temperature=0.5,
    top_p=0.9,
    do_sample=True,
    repetition_penalty=1.3,
)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(response.split("### Response:")[-1].strip())
```

## Training Details

### Training Data

- **Dataset:** [MedQuAD](https://github.com/abachaa/MedQuAD) (Medical Question Answering Dataset)
- **Source:** U.S. National Library of Medicine (NLM)
- **Size:** 16,407 → 16,325 samples (after anonymization of PHI)
- **Language:** English
- **Split:** 90% train (14,692) / 5% val (816) / 5% test (817)

### Training Procedure

#### Preprocessing

1. **Anonymization:** Regex-based removal of PHI (URLs, phones, emails, CPFs, SSNs) - 367 substitutions
2. **Normalization:** UTF-8 NFC encoding, whitespace collapse, truncation at 2,500 chars
3. **Split:** 90/5/5 with seed=42 for reproducibility
4. **Format:** Alpaca-style prompts (`### Instruction:`, `### Response:`)

#### Training Hyperparameters

| Hyperparameter | Value | Justification |
|---|---|---|
| Method | QLoRA (4-bit) + Unsloth | Fits in 40GB A100 GPU |
| LoRA rank (r) | 16 | Balance between capacity and overfitting |
| LoRA alpha | 32 | Convention: alpha = 2 × rank |
| LoRA dropout | 0.05 | Light regularization |
| Target modules | q, k, v, o, gate, up, down | All linear layers |
| Learning rate | 2e-4 | Standard for LoRA (QLoRA paper) |
| LR scheduler | cosine | Smooth decay |
| Warmup steps | 50 | Stable training start |
| Optimizer | adamw_8bit | Memory-efficient |
| Epochs | 2 | Sweet spot for 14k samples |
| Batch size | 2 (per device) | VRAM limit |
| Gradient accumulation | 4 | Effective batch = 8 |
| Max sequence length | 4096 | Fits longest MedQuAD samples |

#### Hardware & Time

- **GPU:** NVIDIA A100-SXM4-40GB (Google Colab Pro)
- **VRAM usage:** ~28 GB / 40 GB
- **Training time:** ~3.5 hours (2 epochs)
- **Peak memory:** ~28 GB GPU

## Evaluation

### Testing Data

- **Validation set:** 816 samples from MedQuAD (model never saw during training)
- **Test set:** 817 samples (also held out)

### Metrics

| Metric | Value | Interpretation |
|---|---|---|
| **Training Loss (final)** | ~0.50 | Model adapted to format |
| **Validation Loss** | **0.5864** | Good generalization |
| **Validation Perplexity** | **2.18** | Excellent (hesitates between ~2 words) |
| **Base Model Perplexity (val)** | 4.31 | Baseline reference |
| **Perplexity Reduction** | **49.4%** | Fine-tuning cut hesitation in half |
| **Train-Val Gap** | 1.47× | Small gap, no harmful overfitting |

### Generalization Tests

15 out-of-distribution tests performed:
- ✅ 5/5 general medical questions (lung cancer, MS, heart disease, etc.)
- ✅ 5/5 modern diseases (COVID-19, mRNA vaccines, dengue, monkeypox, Zika) - model correctly answered about diseases never seen in training
- ⚠️ 2/5 edge cases (empty input, gibberish) showed expected hallucinations

**Conclusion:** No harmful overfitting. The model maintains general medical knowledge while adopting the MedQuAD response style.

## Environmental Impact

- **Hardware Type:** NVIDIA A100-SXM4-40GB
- **Hours used:** ~3.5 hours (training only, not counting evaluation/inference)
- **Cloud Provider:** Google Colab Pro
- **Compute Region:** us-east (estimated)
- **Carbon Emitted:** Estimated ~0.4 kg CO₂eq (based on A100 ~250W × 3.5h × ~0.4 kg CO₂/kWh)

## Technical Specifications

### Model Architecture

- **Architecture:** Transformer decoder (Mistral-7B base)
- **Parameters:** 7.24 billion (base) + ~40 million trainable (LoRA)
- **Context length:** 4096 tokens
- **Tokenizer:** SentencePiece (vocab=32,000)

### Compute Infrastructure

- **Framework:** PyTorch 2.1.0 + CUDA 12.1
- **Libraries:** transformers 4.44.0, peft 0.10.0, bitsandbytes 0.43.3, unsloth
- **Quantization:** 4-bit (NF4) with double quantization

## Citation

### BibTeX

```bibtex
@misc{biomistral-medquad-2026,
  author = {Flamers Team},
  title = {BioMistral-7B Fine-Tuned on MedQuAD for Medical Question Answering},
  year = {2026},
  publisher = {HuggingFace},
  howpublished = {\\url{https://huggingface.co/michelleAnogueira/biomistral-medquad-lora}},
  note = {Tech Challenge FIAP - Phase 3}
}
```

### APA

Flamers Team (2026). *BioMistral-7B Fine-Tuned on MedQuAD for Medical Question Answering*. HuggingFace. https://huggingface.co/michelleAnogueira/biomistral-medquad-lora

## Model Card Authors

Flamers Team (FIAP Tech Challenge Phase 3)

## Model Card Contact

https://github.com/Flamers-Team/MedAssistPro

## Framework versions

- PEFT 0.20.0
- Transformers 4.44.0
- PyTorch 2.1.0+cu121
- Bitsandbytes 0.43.3
- Unsloth (latest)

---

**Disclaimer:** This is an academic project. The model is provided "as-is" without warranty. Not for production medical use without extensive validation, regulatory approval, and ongoing human oversight.
