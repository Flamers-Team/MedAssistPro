# 📚 Guia de Datasets — Tech Challenge Fase 3

> Lista completa de datasets públicos

- ✅ **MedQuAD** (NIH público, ~17k pares Q&A médicos EN)
- ✅ **ChatBulário** (HuggingFace, 68k pares Q&A bulas PT-BR)
- ✅ **CID-10** (DATASUS público, fallback 100 doenças se URL falhar)
- ✅ **Synthetic Clinical Notes** (HuggingFace, 3k notas)

---

## Status atual 

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

** Use o script automático `scripts/setup_data_colab.py` para baixar tudo.

---


### **Synthetic Clinical Notes** (HuggingFace)
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

### **CID-10 (Classificação de Doenças)**
- **Por que**: mapear doenças em PT-BR (CID-10) pra respostas do assistente
- **Link DATASUS oficial**: http://www2.datasus.gov.br/cid10/V2008/descrcsv.htm
- **Download direto (GitHub mirror tratado)**:
```bash
curl -L -o cid10.zip https://github.com/cleytonferrari/CidDataSus/raw/master/CIDImport/Repositorio/Resources/CID10CSV.zip
```
- **Formato**: CSV separado por ponto-e-vírgula

---

### **ChatBulário** (bulas PT-BR — substitui ANVISA)

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


**Por que essa mudança foi crítica**: o `anvisa_medicamentos.csv` original só tinha metadados (ex: "Paracetamol | ANALGESICOS"), o que limitava o RAG a buscar por nome. Com o ChatBulário, o sistema agora responde "efeitos colaterais de paracetamol", "posologia de ibuprofeno", "interação medicamentosa de AAS" — impossível antes.

**Limitação conhecida**: o ChatBulário só cobre medicamentos com bulas completas no Bulário Eletrônico ANVISA. Medicamentos muito novos ou antigos podem estar faltando.

---
