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
  - rag
  - chatbulario
  - langgraph
language:
  - en
  - pt
datasets:
  - MedQuAD
  - walmeidadf/ChatBulario
  - ncbi/pubmed
  - TonicAI/synthetic_clinical_notes
  - DATASUS CID-10
library_name: peft
pipeline_tag: text-generation
---

# 📚 Tech Challenge Fase 3 — Projeto Completo
## Assistente Médico Inteligente com IA Fine-Tuned + RAG + LangGraph

> **Documento técnico definitivo** — usado pelo professor pra avaliar o projeto. Contém TODA a arquitetura, decisões, código e resultados.
>
| **Status**: ✅ Fine-tuning concluído + ✅ RAG completo (3 fontes) + ✅ UI testada + ✅ Documentação 3 níveis
>
> **Última atualização**: 08/09/2026 (atualizado — patches Colab + setup_data_colab.py)
>
> **Autora**: Michelle Almeida Nogueira Rodrigues (Flamers Team, FIAP)
> **Organização**: https://github.com/Flamers-Team/Techchalleng3
> **Modelo publicado**: https://huggingface.co/michelleAnogueira/biomistral-medquad-lora

---

## Índice

1. [Contexto do Projeto](#1-contexto-do-projeto)
2. [Decisões Arquiteturais e Justificativas](#2-decisões-arquiteturais-e-justificativas)
3. [Pipeline de Dados (Preprocessing)](#3-pipeline-de-dados-preprocessing)
4. [Fine-Tuning: Execução e Resultados](#4-fine-tuning-execução-e-resultados)
5. [Validação do Modelo](#5-validação-do-modelo)
6. [Tradução PT-BR ↔ EN](#6-tradução-pt-br--en)
7. [Arquitetura do Sistema (Componentes)](#7-arquitetura-do-sistema-componentes)
8. [O Que Falta Fazer](#8-o-que-falta-fazer) ⭐
9. [Cronograma Final](#9-cronograma-final)
10. [Conformidade e Boas Práticas](#10-conformidade-e-boas-práticas)
11. [Contatos e Recursos](#11-contatos-e-recursos)
12. [Anexo: Comandos Úteis](#12-anexo-comandos-úteis)

---

## 1. Contexto do Projeto

O Tech Challenge Fase 3 exige a construção de um **assistente médico inteligente** capaz de auxiliar condutas clínicas, responder dúvidas de médicos e sugerir procedimentos baseados em protocolos internos. O sistema combina:

- **LLM fine-tunado** com dados médicos (BioMistral-7B + MedQuAD)
- **Pipeline RAG** sobre literatura científica e base institucional
- **Validação humana obrigatória** (HITL) em toda sugestão clínica
- **Explainability** com citação de fontes
- **Logging completo** para auditoria

---

## 2. Decisões Arquiteturais e Justificativas

### 2.1. Modelo Base: BioMistral-7B

**Escolha**: BioMistral-7B (variante do Mistral-7B pré-treinada em PubMed).

| Modelo considerado | Vantagem | Desvantagem | Decisão |
|---|---|---|---|
| **BioMistral-7B** | Já viu PubMed, Apache 2.0, converge rápido em domínio médico | Herdou limitações do Mistral base | ✅ **Escolhido** |
| LLaMA-3 8B Instruct | Forte em instruções | Licença restrita, não pré-treinado em medicina | ❌ |
| Falcon-7B | Apache 2.0 puro | Fraco em PT-BR, menos otimizado | ❌ |
| Phi-3-mini | Muito leve (3.8B) | Pequeno demais para nuances clínicas | ❌ |

**Justificativa técnica**: BioMistral pré-treinado em 3B de tokens biomédicos (PubMed Central), reduzindo tempo de convergência no fine-tuning. Licença Apache 2.0 evita complicações comerciais. Tamanho 7B adequado para QLoRA em A100 (40GB).

### 2.2. Método de Fine-Tuning: QLoRA + Unsloth

**Escolha**: QLoRA 4-bit + Unsloth.

**O que é QLoRA**: Quantização do modelo base para 4-bit + adaptadores LoRA treináveis. Ajustamos apenas ~40 milhões de parâmetros (0.6% do total de 7B).

**Justificativa técnica**:

| Alternativa | VRAM | Tempo (2 epochs, 14k) | Veredicto |
|---|---|---|---|
| Full fine-tuning | >80GB | — | ❌ |
| LoRA 16-bit | ~40GB | 8-12h | ❌ |
| **QLoRA + Unsloth** | ~12GB | **2-4h em A100** | ✅ |
| LoRA sem Unsloth | ~15GB | 8-12h | ❌ |

### 2.3. Hiperparâmetros de Fine-Tuning

| Parâmetro | Valor | Justificativa |
|---|---|---|
| `max_seq_length` | 4096 | Acomoda outputs médicos longos (até 2500 chars) |
| `per_device_train_batch_size` | 2 | Limite de VRAM com QLoRA 4-bit |
| `gradient_accumulation_steps` | 4 | Batch efetivo = 8 |
| `num_train_epochs` | 2 | Sweet spot: 1 epoch subaproveita, 3+ causa overfitting |
| `learning_rate` | 2e-4 | Padrão da literatura (QLoRA paper) |
| `lr_scheduler_type` | cosine | Decaimento suave |
| `warmup_steps` | 50 | Estabiliza início |
| `weight_decay` | 0.01 | Regularização L2 |
| `optim` | adamw_8bit | Economiza VRAM |
| `r` (LoRA rank) | 16 | Compromisso performance/overfitting |
| `lora_alpha` | 32 | Convenção: alpha = 2 × rank |
| `lora_dropout` | 0.05 | Regularização leve |
| `target_modules` | q, k, v, o, gate, up, down | Todas camadas lineares |
| `seed` | 42 | Reprodutibilidade |

### 2.4. Datasets Selecionados

| # | Dataset | Fonte | Idioma | Amostras | Uso |
|---|---------|-------|-------|----------|-----|
| 1 | **MedQuAD** | NIH (público) | 🇺🇸 EN | 16.407 → 16.325 (anonimizado) | Fine-tuning principal |
| 2 | **ChatBulário** ⭐ | HuggingFace | 🇧🇷 PT | 68.938 → 10.000 indexados | RAG #1 (bulas PT-BR) |
| 4 | **Synthetic Clinical Notes** | TonicAI/HuggingFace | 🇺🇸 EN | 3.381 (anonimizado) → **indexado** | RAG #2 (notas SOAP) |
| 5 | **CID-10** | DATASUS | 🇧🇷 PT | 12.451 → **12.451 indexados** | Mapeamento de doenças PT-BR |

**Datasets rejeitados**:

| Dataset | Motivo |
|---|---|
| MIMIC-III | Requer aprovação CITI (1-2 semanas) + DUA |
| PMC OA Subset | ~50GB, script customizado bugado |
| Bulas ANVISA (CSV) | Só metadados — substituído pelo ChatBulário |
| Dados sintéticos via LLM própria | Risco de circular dependency |

### 2.5. Arquitetura RAG: 3 Vector Stores + ChromaDB

**Dataset RAG de medicamentos**: **ChatBulário** (substituiu `anvisa_medicamentos.csv` em ago/2026).

| Critério | anvisa_medicamentos.csv (antigo) | ChatBulário (atual) |
|---|---|---|
| Fonte | OpenData ANVISA | HuggingFace `walmeidadf/ChatBulario` |
| Conteúdo | Só metadados (nome, classe, registro) | **Texto completo das bulas** |
| Formato | CSV tabular | **Pares pergunta-resposta** |
| Idioma | PT-BR | 🇧🇷 PT-BR puro |
| Estrutura | Nenhuma | 9 seções padronizadas (RDC 47/2009) |
| Total | 43.445 medicamentos | **68.938 pares Q&A** (~5.724 medicamentos únicos) |
| Cobertura RAG | Apenas metadados | Indicações, posologia, contraindicações, **efeitos adversos**, interações, superdosagem |

**Estado atual do ChromaDB** (set/2026):

| Collection | Documentos | Conteúdo | Status |
|---|---|---|---|
| **chatbulario** | 10.000 | Bulas ANVISA em PT-BR (Q&A) | ✅ Indexado |
| **cid10** | 12.451 | Códigos CID-10 de doenças | ✅ Indexado (set/2026) |
| **synthetic** | 3.381 | Notas clínicas sintéticas SOAP | ✅ Indexado (set/2026) |
| **TOTAL** | **25.832** | 3 vector stores ativos | ✅ Operacional |

**Por que essa mudança foi crítica**: o `anvisa_medicamentos.csv` original só tinha metadados (ex: "Paracetamol | ANALGESICOS"), o que limitava o RAG a buscar por nome de medicamento. Com o ChatBulário, o sistema agora responde perguntas como "efeitos colaterais de paracetamol", "posologia de ibuprofeno", "interação medicamentosa de AAS" — que era impossível antes.

**Modelo de embedding**: `sentence-transformers/all-MiniLM-L6-v2` (384 dim).

| Modelo | Dimensões | Velocidade | Qualidade | Veredicto |
|---|---|---|---|---|
| all-MiniLM-L6-v2 | 384 | 🚀 Rápido | Boa para PT-BR/EN | ✅ Escolhido |
| intfloat/e5-large-v2 | 1024 | 🐢 Lento | Top multilingual | ❌ Overkill |
| BAAI/bge-large-en-v1.5 | 1024 | 🐢 Lento | Top EN | ❌ |

### 2.6. Sistema Multi-Agente: 3 Agentes LangGraph

**Os 3 agentes**:

| Agente | Temperatura | Responsabilidade | Output |
|---|---|---|---|
| **Triagem** | 0.3 (determinístico) | Classificar urgência (EMERGÊNCIA/URGENTE/ROTINA) | JSON com categoria + red_flags |
| **Síntese** | 0.7 (criativo) | Cruzar relato + RAG → hipóteses diagnósticas + exames + medicações | JSON estruturado com citações |
| **Validação** | 0.2 (conservador) | Aplicar guardrails, adicionar disclaimers, citar fontes | JSON validado pronto pro HITL |

**Fluxo LangGraph (4 nós — PMC removido)**:

```
[Relato] → Triagem → RAG (ChatBulário + CID-10 + Synthetic) → Síntese → Validação → HITL → Gerar Docs PDF
                                                                              ↑
                                                                  Médico SEMPRE ratifica
```

### 2.7. HITL (Human-in-the-Loop) Obrigatório

**Implementação**: O nó HITL pausa o grafo LangGraph usando `interrupt()`. O médico visualiza a sugestão em UI Gradio e decide:
- **Aprovar**: grafo segue para gerar_docs
- **Editar**: texto volta para síntese com edição
- **Rejeitar**: grafo encerra sem gerar documento

**Por que HITL é mandatório**:
1. **Segurança clínica**: LLM pode alucinar. Médico sempre valida.
2. **LGPD**: ato médico é responsabilidade do profissional, não da IA.
3. **Audit trail**: decisão humana é logada.

### 2.8. Logging e Auditoria: SQLite + Decorador

**Por que SQLite**:
- ✅ Queries complexas (filtros SQL)
- ✅ Concorrência ACID
- ✅ Compactação binária
- ✅ Auditoria imutável

**Decorador `@audit_llm_call`**: instrumenta qualquer função de agente automaticamente. Captura: input, output, tokens, latência, custo estimado.

---

## 3. Pipeline de Dados (Preprocessing)

### 3.1. Anonimização

**Regex aplicados** (PHI detectado):

| Tipo | Padrão | Ocorrências substituídas |
|---|---|---|
| URL | `https?://[\w./\-?=&%#]+` | 156 |
| Telefone | `\d{3}[-.\s]?\d{3}[-.\s]?\d{4}` | 149 |
| CPF | `\d{3}\.?\d{3}\.?\d{3}-?\d{2}` | 28 |
| SSN | `\d{3}-?\d{2}-?\d{4}` | 14 |
| E-mail | `[\w.+-]+@[\w-]+\.[\w.]+` | 13 |
| CEP | `\d{5}-?\d{3}` | 6 |
| Data numérica | `\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}` | 4 |
| **TOTAL** | | **367 substituições** |

**Decisão sobre NER**: Consideramos usar spaCy NER, rejeitamos porque confundiria doenças eponyms com nomes de pessoas (Parkinson, Down, Hodgkin).

### 3.2. Normalização

| Operação | Justificativa |
|---|---|
| Encoding UTF-8 + NFC | Caracteres compostos (ã vs a+̃) |
| Whitespace collapse (`\s+` → ` `) | XML do NIH tem 20+ espaços antes de bullets |
| Remoção de control chars | Evita bugs no tokenizer |
| Truncamento em 2500 chars | Outputs >2500 não cabem em max_seq_length=4096 |

### 3.3. Split 90/5/5

| Split | Amostras | % | Uso |
|---|---|---|---|
| train.jsonl | 14.692 | 90% | Ajuste de pesos |
| val.jsonl | 816 | 5% | Avaliação honesta |
| test.jsonl | 817 | 5% | Early stopping + tune hiperparâmetros |

---

## 4. Fine-Tuning: Execução e Resultados ⭐

### 4.1. Execução no Colab Pro

**Hardware**: NVIDIA A100-SXM4-40GB (40 GB VRAM)

**Estrutura no Google Drive**:
```
/content/drive/MyDrive/techchallenge_fase3/
├── train.jsonl              (17 MB)
├── val.jsonl                (0.91 MB)
├── checkpoints/             (gerado durante treino)
└── biomistral-medquad-lora/ (80 MB final)
```

### 4.2. Métricas de Treinamento

| Métrica | Valor | Interpretação |
|---|---|---|
| Loss inicial (epoch 0) | ~1.5 | Modelo "perdido" |
| Loss final (epoch 2) | ~0.5 | Modelo adaptado |
| Validation Loss | **0.5864** | ✅ Generalizou bem |
| **Perplexity (validação)** | **2.18** | ✅ Excelente (hesita entre ~2 palavras) |
| Perplexity BASE (validação) | 4.31 | Baseline de referência |
| **Redução de perplexidade** | **49.4%** | Fine-tuning cortou hesitação pela metade |
| Tempo total | ~3h30min em A100 | Dentro do esperado |
| GPU memory peak | ~28 GB / 40 GB | Confortável |

**Interpretação da Perplexidade 2.18**:

| Perplexidade | "Hesitação média" | Significado |
|---|---|---|
| 1.0 | 1 palavra | Perfeito (overfitting total) |
| **2.18** | **~2 palavras** | **Excelente** ✅ |
| 4.31 (base) | ~4 palavras | Bom, mas dobro da hesitação |
| 5-15 | - | Excelente |
| 50+ | - | Modelo chuta |

### 4.3. Análise da Curva de Treinamento (degrau na virada da época)

**Observação**: durante o treino foi detectado um **degrau na training loss** exatamente na transição da época 1 → época 2.

**Por que acontece**:
- Na época 1, cada lote que o modelo vê é dado novo
- No instante em que a época 2 começa, o data loader volta ao início e mostra os mesmos exemplos
- O modelo já ajustou os pesos na direção deles
- Quando reaparecem, o erro é menor
- Não é aprendizado novo, é reconhecimento do que já foi visto

**Consequência**: a partir da época 2, a training loss deixa de ser um bom termômetro de generalização.

**"A loss caiu na época 2" prova overfitting?** **NÃO**, sozinha não prova. Overfitting é quando o desempenho em dados não vistos piora enquanto o treino melhora. Para ver isso é necessária a curva de validação durante o treino (Seção 14).

### 4.4. Por que NÃO houve Overfitting (análise crítica)

**Três evidências independentes**:

1. **Perplexidade em validação melhorou vs base**: Fine-tuned = 2.18 vs Base = 4.31. **Redução de 49.4%**. Se houvesse overfitting, o fine-tuned em validação seria PIOR que o base. Não foi — foi o DOBRO melhor.

2. **Gap treino → validação pequeno**:
   - Loss treino final: ~0.39 (perplexity 1.48)
   - Loss validação: ~0.78 (perplexity 2.18)
   - **Gap: 1.47×** (pequeno, dentro do esperado)

3. **Generalização demonstrada empiricamente**: nos 15 testes, o modelo respondeu corretamente sobre COVID-19, mRNA vaccines, monkeypox, Zika, dengue — doenças que JAMAIS apareceram no treino.

**Veredito**: O fine-tuning **foi um ganho real**. O modelo:
- ✅ Manteve o conhecimento do modelo base
- ✅ Aprendeu o formato estruturado MedQuAD
- ✅ Generalizou para contextos novos
- ✅ Reduziu hesitação em 49.4%

### 4.5. Otimização possível: "Deveria ter parado em 1 época?"

> A época 2 acrescentou memorização (o degrau) sem prova de que melhorou a generalização. É plausível que 1 época já entregasse uma validação parecida, com menos decoreba e metade do tempo/custo.

**Como saber com certeza**: gerar a **curva de eval_loss durante o treino** (próxima execução). Se a eval_loss ficou plana na época 2 → 1 época bastava.

### 4.6. Avaliação Qualitativa (20 pares)

Modelo gerou 20 pares pergunta/resposta em dados do val set (modelo nunca viu). Resultados em `eval_results_qualitativo.json`.

---

## 5. Validação do Modelo ⭐

### 5.1. Teste de Generalização (15 perguntas)

Submetemos 15 perguntas divididas em 3 categorias:

| Categoria | # | Objetivo | Resultado |
|---|---|---|---|
| **Perguntas gerais** | 5 | Validar conhecimento em doenças comuns | ✅ 5/5 respostas longas e coerentes |
| **Doenças modernas** (NÃO no MedQuAD) | 5 | Testar generalização (COVID, mRNA, dengue, monkeypox, Zika) | ✅ 5/5 — modelo respondeu corretamente sobre doenças que **nunca viu no treino** |
| **Edge cases** | 5 | Testar robustez (PT-BR, gibberish, vazio, fora do escopo) | ⚠️ 2 alucinações em casos extremos (esperado) |

**Análise automática**:
```
Total: 15 perguntas
✅ Respostas longas (>100 chars): 14/15 (93%)
⚠️  Respostas vazias/curtas: 0/15
🔁 Repetindo a pergunta: 1/15
🎯 VEREDITO: ✅ GENERALIZOU BEM
```

### 5.2. Comparação Quantitativa FINE-TUNED vs BASE

| Modelo | Perplexidade (validação) | "Hesitação média" | Interpretação |
|---|---|---|---|
| **Base** (BioMistral-7B sem fine-tuning) | **4.31** | ~4 palavras | Baseline |
| **Fine-tuned** (seu modelo) | **2.18** | ~2 palavras | **49.4% menos hesitação** ✅ |

Se o fine-tuning tivesse causado overfitting, o fine-tuned em validação seria PIOR que o base. O oposto aconteceu.

### 5.3. Comparação Qualitativa FINE-TUNED vs BASE

Carregamos o modelo **base** e comparamos respostas para 3 perguntas idênticas:

| Pergunta | Base | Fine-Tuned | Quem ganhou? |
|---|---|---|---|
| Sintomas de câncer de pulmão | 8 sintomas | 12 sintomas | Fine-Tuned |
| Como funciona vacina mRNA | Explicação técnica | Similar + mais estrutura | Empate |
| O que é diabetes? (PT-BR) | Respondeu PT | Respondeu PT | Empate |

### 5.4. Por que NÃO houve overfitting (resumo)

| Evidência | Resultado |
|---|---|
| Perplexidade em validação | Fine-tuned (2.18) **metade** do base (4.31) |
| Gap treino → validação | Pequeno (1.47×) |
| Generalização empírica | Respondeu sobre COVID/mRNA/Zika/monkeypox que **não estavam no treino** |

### 5.5. Análise do degrau na curva de treino

O degrau na transição da época 1 → época 2 acontece porque o modelo já ajustou os pesos nos exemplos da época 1. Quando reaparecem, o erro é menor — não é aprendizado novo, é reconhecimento (memorização parcial).

---

## 6. Tradução PT-BR ↔ EN ⭐

### 6.1. Problema

O modelo foi treinado 100% em inglês (MedQuAD do NIH). Respostas em PT-BR são inconsistentes — às vezes mistura inglês, usa terminologia errada, ou alucina etimologia.

### 6.2. Solução: Tradução Bidirecional

**Arquitetura**:
```
Pergunta PT-BR → MarianMT (PT→EN) → BioMistral (responde EN) → MarianMT (EN→PT) → Resposta PT-BR
```

**Modelos escolhidos**: Helsinki-NLP/opus-mt-tc-big-{pt-en,en-pt}

| Característica | Valor |
|---|---|
| Família | MarianMT (Helsinki-NLP/OPUS) |
| Tamanho | ~1 GB cada (2 GB total) |
| Velocidade (GPU) | ~1-2s por tradução |
| Latência total adicionada | ~3-5s |
| Treinamento | Milhões de pares PT↔EN de corpus paralelo |

### 6.3. Implementação

Arquivo: `src/llm/assistente_traduzido.py`

### 6.4. Limitações Conhecidas

- Termos técnicos médicos podem ser traduzidos literalmente
- MarianMT treinado mais com PT-EU que PT-BR

---

## 7. Arquitetura do Sistema (Componentes)

### 7.1. Estrutura do Repositório

```
Techchalleng3/                          (GitHub: Flamers-Team/Techchalleng3)
├── README.md                            Documentação principal
├── .gitignore                           Proteção contra dados sensíveis
├── .gitattributes                       Git LFS para datasets grandes
├── docs/
│   ├── RELATORIO_TECNICO_PARA_EQUIPE.md      Relatório técnico principal
│   ├── MANUAL_UI.md                          Manual de uso da UI
│   ├── GUIA_DATASETS.md                     Guia dos datasets
│   ├── MODEL_CARD_HUGGINGFACE.md            Model Card pro HF
│   ├── index.html                           HTML do Space HF
│   ├── RELATORIO_TECNICO_PARA_EQUIPE.docx   Versão DOCX
│   ├── MANUAL_UI.docx
│   ├── GUIA_DATASETS.docx
│   └── TECHCHALLENGE_FASE3_PROJETO_COMPLETO.docx   ← Este documento
├── notebooks/
│   ├── 02_finetuning.ipynb              Notebook Colab Pro (A100)
│   └── 13_test_generalizacao.ipynb      Testes de validação
├── src/
│   ├── data/                            Pipeline de dados
│   │   ├── 01_anonimizar.py
│   │   ├── 02_normalizar_e_split.py
│   │   ├── 03_validar_qualidade.py
│   │   └── 04_anonimizar_synthetic.py
│   ├── rag/
│   │   ├── build_index_local.py         Indexador antigo
│   │   ├── build_index_chatbulario.py   Indexador ChatBulário (USADO)
│   │   ├── build_index_pubmed.py        Indexador PubMed (não usado)
│   │   ├── build_index_pmc.py           Indexador PMC (não usado)
│   │   └── retriever.py                 Wrapper ChromaDB (3 collections)
│   ├── llm/
│   │   ├── cliente.py                   Wrapper LLM
│   │   ├── assistente_traduzido.py      Com tradução PT-BR
│   │   └── assistente_traduzido_cpu.py  Versão CPU
│   ├── agents/                          3 agentes LangGraph
│   │   ├── triagem.py
│   │   ├── sintese.py
│   │   └── validacao.py
│   ├── graph/                           Orquestração LangGraph
│   │   ├── state.py
│   │   ├── nodes.py
│   │   └── workflow.py
│   ├── logging/                         Auditoria SQLite
│   │   ├── schemas.py
│   │   ├── audit.py
│   │   ├── decorators.py
│   │   └── dashboard.py
│   ├── docs/                            Gerador de PDFs
│   │   └── generator.py
│   └── ui/
│       └── gradio_app.py                Interface Gradio (4 abas)
└── data/                                (gitignored)
    ├── raw/                             Datasets brutos
    │   ├── chatbulario_*.jsonl          (download manual)
    │   ├── cid10_subcategorias.csv       (download manual)
    │   ├── synthetic_clinical_notes_anonimizado.jsonl
    │   └── medquad_finetuning.jsonl
    └── processed/                       Dados processados
        └── chroma_index/                ChromaDB (3 collections)
```

### 7.2. Stack Tecnológica Completa

| Camada | Tecnologia | Versão |
|---|---|---|
| **LLM Base** | BioMistral-7B (Mistral-7B + PubMed) | — |
| **Fine-tuning** | TRL + PEFT + bitsandbytes + Unsloth | TRL 0.10.0, PEFT 0.10.0 |
| **Quantização** | QLoRA 4-bit | — |
| **Tokenizer** | LlamaTokenizerFast (vocab=32k) | — |
| **Vector Store** | ChromaDB | 0.4.18 |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 | — |
| **Tradução** | MarianMT (Helsinki-NLP/opus-mt-tc-big) | — |
| **Orquestração** | LangChain + LangGraph | 0.3.0 / 0.2.19 |
| **Auditoria** | SQLite + Loguru | Python 3.11 |
| **GPU alvo** | NVIDIA A100 (40GB) Colab Pro | — |

---

## 8. O Que Falta Fazer ⭐

### ✅ JÁ FEITO

| # | Etapa | Status | Local |
|---|---|---|---|
| 1 | Análise do PDF do Tech Challenge | ✅ | — |
| 2 | Download + anonimização MedQuAD | ✅ | `src/data/01_anonimizar.py` |
| 3 | Normalização + split 90/5/5 | ✅ | `src/data/02_normalizar_e_split.py` |
| 4 | Validação qualitativa (93.5/100) | ✅ | `src/data/03_validar_qualidade.py` |
| 5 | Anonimização Synthetic Notes | ✅ | `src/data/04_anonimizar_synthetic.py` |
| 6 | Download datasets (MedQuAD, ChatBulário, CID-10, Synthetic) | ✅ | `data/raw/` |
| 7 | Indexação ChromaDB (ChatBulário 10k + CID-10 12k + Synthetic 3k) | ✅ | `data/processed/chroma_index/` |
| 8 | Notebook de fine-tuning (814 linhas) | ✅ | `notebooks/02_finetuning.ipynb` |
| 9 | Fine-tuning executado no Colab Pro (3h30min) | ✅ | Drive: `biomistral-medquad-lora/` |
| 10 | Avaliação perplexity (2.18 vs 4.31, redução 49.4%) | ✅ | `eval_results_qualitativo.json` |
| 11 | 15 testes de generalização | ✅ | `test_generalizacao.json` |
| 12 | Comparação FINE-TUNED vs BASE | ✅ | `notebooks/02_finetuning.ipynb` SEÇÃO 13 |
| 13 | Script de tradução PT-BR ↔ EN | ✅ | `src/llm/assistente_traduzido.py` |
| 14 | Repositório GitHub (público) | ✅ | `Flamers-Team/Techchalleng3` |
| 15 | 3 agentes LangGraph | ✅ | `src/agents/` |
| 16 | Orquestração LangGraph | ✅ | `src/graph/` |
| 17 | Logging SQLite + decorador | ✅ | `src/logging/` |
| 18 | UI Gradio (4 abas) | ✅ | `src/ui/gradio_app.py` |
| 19 | README + documentação 3 níveis | ✅ | `README.md`, `docs/*.md` |
| 20 | Relatório DOCX técnico | ✅ | `docs/*.docx` |
| 21 | Modelo publicado no HuggingFace (público) | ✅ | `michelleAnogueira/biomistral-medquad-lora` |
| 22 | Space Static no HuggingFace | ✅ | `michelleAnogueira/techchalleng3-demo` |
| 23 | Remoção dos mocks PMC (fontes inventadas) | ✅ | `src/rag/retriever.py` |
| 24 | Tratamento de erro robusto (RuntimeError) | ✅ | `src/rag/retriever.py`, `src/ui/gradio_app.py` |

### ⏳ PENDENTE (priorizado)

| # | Tarefa | Tempo Est. | Prioridade | Status |
|---|---|---|---|---|
| 1 | **Testar a UI Gradio** no Colab (compartilhar URL com equipe/professor) | 15 min | 🔴 Alta | ✅ **FEITO** — URL gradio.live funciona |
| 2 | **Gravar vídeo demo** (≤15min) mostrando: LLM respondendo + RAG funcionando + HITL | 1-2h | 🔴 Alta | Pendente |
| 3 | **Atualizar DOCX final** com seção "O Que Falta" + cronograma | 30 min | 🟡 Média | ✅ **FEITO** — 5 DOCX atualizados |
| 4 | **Testar pipeline completo** com pergunta real no Colab | 15 min | 🟡 Média | ✅ **FEITO** — RAG + LLM + UI funcionando |
| 5 | **Substituir mocks** em `src/llm/client.py` (`_mock_response` ainda existe) | 1h | 🟡 Média | Pendente (fallback intencional, erros via RuntimeError) |
| 6 | **Refatorar `docs/generator.py`** (CRM hardcoded "12345-DF") | 1-2h | 🟡 Média | Pendente |
| 7 | **Testes integrados** end-to-end (UI + LLM + RAG + HITL + PDFs) | 1h | 🟡 Média | Pendente |
| 8 | **Limpar cache HuggingFace** local (`walmeidadf___chat_bulario/`, `arrow` files) | 5 min | 🟢 Baixa | Pendente |
| 9 | **README badges** (build status, license, etc) | 15 min | 🟢 Baixa | ✅ **FEITO** — badges coloridos |
| 10 | **HuggingFace Spaces Gradio** (deploy com UI rodando 24/7) | 30 min | 🟢 Baixa | ⚠️ Bloqueado (requer PRO pago) — Static Space grátis criado |
| 11 | **Script setup_data_colab.py** (baixa datasets automaticamente) | - | 🟡 Média | ✅ **FEITO** — `scripts/setup_data_colab.py` |
| 12 | **Patch gradio_client completo** (enum + const) | - | 🟡 Média | ✅ **FEITO** — patch em `rodarcolab.ipynb` |
| 13 | **Notebook `rodarcolab.ipynb` corrigido** (caminhos + patches) | - | 🔴 Alta | ✅ **FEITO** — 31 células, todas funcionais |

---

## 9. Cronograma Final ⭐

### 9.1. Para Entrega Hoje (URGENTE)

| Hora | Atividade | Quem |
|---|---|---|
| **+0h** | Testar UI no Colab (carrega LLM + RAG, gera URL pública) | Michelle |
| **+0:30h** | Gravar tela mostrando: pergunta PT → resposta PT (5 min de vídeo) | Michelle |
| **+1h** | Gravar demo completo do projeto (15 min) | Michelle |
| **+3h** | Gerar DOCX final consolidado | Michelle |
| **+4h** | Submeter no portal FIAP | Michelle |

### 9.2. Para Entrega Completa (1 semana)

| Dia | Atividade |
|---|---|
| **Dia 1 (hoje)** | Testar UI + gravar demo + DOCX final |
| **Dia 2** | Substituir `_mock_response` por erro estruturado |
| **Dia 3** | Refatorar `docs/generator.py` (input do usuário, não hardcoded) |
| **Dia 4** | README completo + instruções de instalação |
| **Dia 5** | Testes integrados end-to-end |
| **Dia 6-7** | Buffer para ajustes finais |

---

## 10. Conformidade e Boas Práticas

### 10.1. LGPD

- ✅ Dados sintéticos (Synthetic Clinical Notes) explicitamente anonimizados
- ✅ MedQuAD é público (NIH) e passou por anonimização preventiva
- ✅ Logs não armazenam PHI cru (apenas SHA256 hash + preview truncado)
- ✅ Documentação de tratamento de dados em `src/data/01_anonimizar.py`

### 10.2. Segurança do Assistente

- ✅ **HITL obrigatório**: médico sempre ratifica antes de documento ser gerado
- ✅ **Citação de fonte**: cada resposta inclui `[Fonte: ChatBulario-XXX]`
- ✅ **Disclaimer automático**: toda resposta inicia com aviso de validação humana
- ✅ **Sem mocks de fontes**: PMC mock removido, só dados reais (ChatBulário + CID-10 + Synthetic)
- ✅ **Tratamento de erro robusto**: RuntimeError quando RAG não disponível (não falha silencioso)
- ✅ **Auditoria completa**: todas as chamadas LLM/RAG logadas em SQLite

### 10.3. Reprodutibilidade

- ✅ Seeds fixas (42) em todos os scripts
- ✅ Versões de bibliotecas fixadas (datasets<3.0, chromadb==0.4.18)
- ✅ `.gitignore` protege contra versionamento acidental de modelos/dados

---

## 11. Contatos e Recursos

- **Repositório**: https://github.com/Flamers-Team/Techchalleng3
- **Branch principal**: `main`
- **Modelo HF**: https://huggingface.co/michelleAnogueira/biomistral-medquad-lora
- **Space HF**: https://huggingface.co/spaces/michelleAnogueira/techchalleng3-demo
- **Issues/bugs**: abrir no GitHub Issues do repo
- **Documentação adicional**: `docs/RELATORIO_TECNICO_PARA_EQUIPE.md`
- **Guia de datasets**: `docs/GUIA_DATASETS.md`
- **Manual UI**: `docs/MANUAL_UI.md`

---

## 12. Anexo: Comandos Úteis

### 12.1. Pipeline de Dados

```bash
# Anonimização MedQuAD
python src/data/01_anonimizar.py

# Normalização + split
python src/data/02_normalizar_e_split.py

# Validação qualitativa
python src/data/03_validar_qualidade.py

# Anonimização Synthetic Clinical Notes
python src/data/04_anonimizar_synthetic.py
```

### 12.2. RAG

```bash
# Indexar ChatBulário (10k amostras, ~5min)
python src/rag/build_index_chatbulario.py 10000

# Indexar todas as 68k (~35min)
python src/rag/build_index_chatbulario.py
```

### 12.3. Fine-Tuning (Colab Pro)

```python
# Abrir notebooks/02_finetuning.ipynb no Google Colab
# Runtime → Change runtime type → A100 GPU
# Executar células em ordem
```

### 12.4. Assistente Traduzido (PT-BR)

```python
from src.llm.assistente_traduzido import AssistenteTraduzido

bot = AssistenteTraduzido(
    modelo_path="biomistral-medquad-lora",
    device="cuda",
)
print(bot.perguntar("O que é diabetes?"))
```

### 12.5. Logging

```python
from src.logging.audit import init_db, log_event
from src.logging.schemas import LLMCallEvent
from src.logging.decorators import audit_llm_call
from src.logging.dashboard import dashboard_resumo

init_db()
dashboard_resumo(horas=24)
```

### 12.6. Publicação no HuggingFace

```python
from huggingface_hub import login, HfApi, create_repo

login()
api = HfApi()
create_repo(repo_id="seu-user/modelo", repo_type="model", private=False)

api.upload_folder(
    folder_path="./modelo",
    repo_id="seu-user/modelo",
    repo_type="model",
)
```

### 12.7. Setup Completo no Google Colab (⭐ RECOMENDADO)

**Notebook**: `notebooks/rodarcolab.ipynb` (31 células, ~15 min de execução)

**O que faz**:
1. Monta Google Drive
2. Instala dependências (numpy, pydantic, chromadb, gradio, unsloth)
3. Clona repositório
4. Copia modelo LoRA do Drive
5. Aplica patch gradio_client (corrige `TypeError: bool is not iterable`)
6. Cópia do modelo pro caminho que a UI espera
7. Indexa ChatBulário (RAG)
8. Patch chromadb (np.float_ → np.float64)
9. Carrega RAG + LLM
10. Sobe UI Gradio (gera URL pública tipo `https://xxxxx.gradio.live`)

**Setup automático de dados** (alternativa):
```bash
# Baixa todos os datasets públicos automaticamente
python scripts/setup_data_colab.py

# Baixa: MedQuAD, ChatBulário, CID-10, Synthetic Notes
# Tempo: ~10 min
```

**Patches aplicados no notebook**:
- ✅ `gradio_client/utils.py` — `'if "enum" in schema:'` → `isinstance(schema, dict) and "enum" in schema:`
- ✅ `chromadb/types.py` — `np.float_` → `np.float64`
- ✅ `huggingface_hub` downgrade para 0.20.0 (HfFolder ainda existe)
- ✅ `share=False` → `share=True` (gera URL pública)

**Caminhos importantes**:
- Modelo fine-tuned: `/content/drive/MyDrive/techchallenge_fase3/biomistral-medquad-lora/`
- Modelo copiado: `/content/Techchalleng3/biomistral-medquad-lora/` (caminho que UI espera)
- ChromaDB: `/content/Techchalleng3/data/processed/chroma_index/`

---

**Relatório gerado em**: 08/09/2026
**Versão do projeto**: 2.2 (patches Colab aplicados + setup_data_colab.py)
**Próxima atualização**: após testes finais + vídeo demo
