# 📚 Guia de Datasets — Tech Challenge Fase 3

> Lista completa de datasets públicos que você precisa baixar, com links diretos e instruções.

## ⚡ Setup Automático (⭐ RECOMENDADO)

```bash
# Baixa automaticamente TODOS os datasets públicos
python scripts/setup_data_colab.py
```

**O que baixa**:
- ✅ **MedQuAD** (NIH público, ~17k pares Q&A médicos EN)
- ✅ **ChatBulário** (HuggingFace, 68k pares Q&A bulas PT-BR)
- ✅ **CID-10** (DATASUS público, fallback 100 doenças se URL falhar)
- ✅ **Synthetic Clinical Notes** (HuggingFace, 3k notas)

**Tempo**: ~10 min

---

## 🎯 Status atual (set/2026)

| # | Dataset | Status | Onde baixar | Uso |
|---|---------|--------|-------------|-----|
| ✅ | **MedQuAD** | Baixar via `scripts/setup_data_colab.py` ou `git clone https://github.com/abachaa/MedQuAD` | NIH (público) | Fine-tuning |
| ✅ | **ChatBulário** ⭐ | Baixar via `scripts/setup_data_colab.py` ou `load_dataset("walmeidadf/ChatBulario")` | HuggingFace | **RAG #1 (bulas PT-BR)** |
| ✅ | **Synthetic Clinical Notes** | Baixar via `scripts/setup_data_colab.py` | TonicAI/HuggingFace | RAG #3 (notas SOAP) |
| ✅ | **CID-10 DATASUS** | Baixar via `scripts/setup_data_colab.py` (fallback: 100 doenças comuns) | DATASUS (público) | RAG #2 (mapeamento doenças) |
| 🗑️ | ~~ANVISA Medicamentos (CSV)~~ | ~~REMOVIDO ago/2026 — substituído por ChatBulário~~ | — | ~~RAG metadados~~ |
| 🗑️ | ~~LiveQA-Med~~ | ~~REMOVIDO set/2026 — substituído pelos 15 testes do notebook~~ | — | ~~Avaliar RAG~~ |
| 🗑️ | ~~PubMedQA~~ | ~~REMOVIDO set/2026 — não usado no pipeline final~~ | — | ~~Complementar fine-tuning~~ |
| 🗑️ | ~~PMC Open Access~~ | ~~REMOVIDO — URL quebrada (mudou em abril/2026)~~ | — | ~~RAG #1 literatura~~ |
| ⚠️ | **MIMIC-III** | REJEITADO (requer aprovação + DUA) | — | Fine-tuning (burocracia) |

**⭐ ATUALIZAÇÃO SET/2026**: Limpeza completa do repositório. Agora só temos 4 datasets ativos. Os demais foram removidos do `data/raw/` (liberou ~500 MB). Use o script automático `scripts/setup_data_colab.py` para baixar tudo.

---

## 📥 Downloads prioritários

> ⚠️ **SET/2026**: Seções 1 (PubMedQA), 2 (PMC) e 3 (ANVISA) foram removidas — esses datasets não fazem mais parte do pipeline. Use o **Setup Automático** no topo (`scripts/setup_data_colab.py`) ou siga as instruções das seções 4-6 abaixo para cada dataset ativo.

### 4. **Synthetic Clinical Notes** (HuggingFace)
- **Por que**: anotações clínicas sintéticas pra RAG e fine-tuning
- **Melhor opção**: https://huggingface.co/datasets/TonicAI/synthetic_clinical_notes
  - 3.38k notas prontas, formato SOAP, **sem PHI**
  - Licença aberta
- **Alternativa maior**: https://huggingface.co/datasets/IntelLabs/SynthClinicalNotes
  - 1410 trajetórias completas de internação (multi-dia)
- **Download via Python**:
```python
from datasets import load_dataset
ds = load_dataset("TonicAI/synthetic_clinical_notes")
```

### 5. **CID-10 (Classificação de Doenças)**
- **Por que**: mapear doenças em PT-BR (CID-10) pra respostas do assistente
- **Link DATASUS oficial**: http://www2.datasus.gov.br/cid10/V2008/descrcsv.htm
- **Download direto (GitHub mirror tratado)**:
```bash
curl -L -o cid10.zip https://github.com/cleytonferrari/CidDataSus/raw/master/CIDImport/Repositorio/Resources/CID10CSV.zip
```
- **Formato**: CSV separado por ponto-e-vírgula

---

### 5. ⭐ **ChatBulário** (bulas PT-BR — substitui ANVISA)

- **Por que**: dataset que combina **todas as bulas de medicamentos ANVISA em formato pergunta-resposta em PT-BR**. Resolveu o problema do RAG multilíngue (que tinha ANVISA só com metadados + outras bases em inglês).
- **Fonte**: https://huggingface.co/datasets/walmeidadf/ChatBulario
- **Tamanho**: ~200 MB (3 splits JSONL)
- **Formato**: JSONL com 18 colunas (nome, classe, princípio ativo, **pergunta**, **resposta**, seção, etc)
- **Total**: **68.938 pares Q&A** (~5.724 medicamentos únicos × ~12 perguntas cada)
- **9 seções padronizadas** (RDC 47/2009):
  1. Para que é indicado
  2. Como funciona
  3. Quando não usar (contraindicações)
  4. Cuidados antes de usar
  5. Interações medicamentosas
  6. Como usar (posologia)
  7. Efeitos adversos
  8. O que fazer se esquecer
  9. Superdosagem

**Download via Python**:
```python
from datasets import load_dataset

# Baixa pra data/raw/
ds = load_dataset(
    "walmeidadf/ChatBulario",
    cache_dir="data/raw"
)

# Salvar em JSONL
import json
for split in ["train", "validation", "test"]:
    with open(f"data/raw/chatbulario_{split}.jsonl", "w", encoding="utf-8") as f:
        for sample in ds[split]:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
```

**Indexar no ChromaDB**:
```bash
# Indexar TODAS as 68k (demora ~35min em CPU)
python src/rag/build_index_chatbulario.py

# OU só 10k pra teste rápido (~5min)
python src/rag/build_index_chatbulario.py 10000
```

**Por que essa mudança foi crítica**: o `anvisa_medicamentos.csv` original só tinha metadados (ex: "Paracetamol | ANALGESICOS"), o que limitava o RAG a buscar por nome. Com o ChatBulário, o sistema agora responde "efeitos colaterais de paracetamol", "posologia de ibuprofeno", "interação medicamentosa de AAS" — impossível antes.

**Limitação conhecida**: o ChatBulário só cobre medicamentos com bulas completas no Bulário Eletrônico ANVISA. Medicamentos muito novos ou antigos podem estar faltando.

---

## 📦 Datasets opcionais (tempo permitir)

### 6. **MIMIC-III** (REJEITADO — burocrático)
- **Por que**: prontuários reais anonimizados (UTI Beth Israel)
- **Link**: https://mimic.mit.edu/docs/faq/how-to-get-access.html
- **⚠️ Rejeitado**: requer curso CITI + aprovação PhysioNet (1-2 semanas). Não compensa pro Tech Challenge.
- **Tamanho**: ~6 GB compactado

> ⚠️ **SET/2026**: Seções 6 (RxNorm), 7 (DrugBank) foram removidas — não usadas no pipeline. Apenas MIMIC-III é mencionado como rejeitado por questões burocráticas.

---

## 🎯 Plano de ação sugerido (set/2026)

**Recomendação**: use o script automático — faz tudo em 10 min sem erro:

```bash
python scripts/setup_data_colab.py
```

### Manual (se preferir controle individual)

```bash
# 1. MedQuAD (~23MB processado)
git clone https://github.com/abachaa/MedQuAD.git
python src/data/01_anonimizar.py  # converte para medquad_finetuning.jsonl

# 2. ChatBulário (~200MB, 68k pares Q&A)
python -c "from datasets import load_dataset; ds = load_dataset('walmeidadf/ChatBulario', cache_dir='data/raw')"

# 3. Synthetic Clinical Notes (~11MB, 3k notas)
python -c "from datasets import load_dataset; load_dataset('TonicAI/synthetic_clinical_notes')"

# 4. CID-10 (~1.3MB ou fallback 100 doenças)
curl -L -o data/raw/cid10_subcategorias.csv \
  https://raw.githubusercontent.com/cleytonferrari/CidDataSus/master/CIDImport/Repositorio/Resources/CID-10-CAPITULOS.CSV
```

### Tempo total

| Etapa | Tempo |
|---|---|
| Setup automático (1 comando) | ~10 min |
| Manual (4 comandos separados) | ~15 min |

---

## 📁 Onde salvar no projeto (estrutura atual set/2026)

Todos os datasets ficam em `data/raw/` (protegido pelo `.gitignore`):

```
data/
├── raw/
│   ├── medquad_finetuning.jsonl           ✅ ativo (fine-tuning)
│   ├── chatbulario_train.jsonl            ✅ ativo (RAG #1, 10k indexadas)
│   ├── chatbulario_validation.jsonl       ✅ ativo (avaliação)
│   ├── chatbulario_test.jsonl             ✅ ativo (avaliação)
│   ├── synthetic_clinical_notes/          ✅ ativo (RAG #3, 1k notas)
│   └── cid10_subcategorias.csv            ✅ ativo (RAG #2)
└── processed/
    ├── train.jsonl                        ✅ (fine-tuning splits)
    ├── val.jsonl                          ✅
    ├── test.jsonl                         ✅
    ├── synthetic_clinical_notes_anonimizado.jsonl  ✅
    └── chroma_index/                      ✅ (ChromaDB indexado)
        ├── chatbulario/    (10k docs)
        ├── cid10/          (22 códigos)
        └── synthetic/      (1k notas)
```

---

## ✅ Checklist de downloads (set/2026)

- [x] **MedQuAD** (via `scripts/setup_data_colab.py`)
- [x] **ChatBulário** (via `scripts/setup_data_colab.py`)
- [x] **Synthetic Clinical Notes** (via `scripts/setup_data_colab.py`)
- [x] **CID-10** (via `scripts/setup_data_colab.py` com fallback)
- [x] **ChromaDB indexado** (via `python src/rag/build_index_chatbulario.py 10000`)

**Tudo automatizado** — basta rodar `scripts/setup_data_colab.py` no Colab.