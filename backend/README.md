# Backend

API FastAPI do Assistente Médico IA (agentes, RAG, LangGraph, geração de documentos, auditoria).

## Estrutura

```text
backend/
├── src/
│   ├── api/        # FastAPI app e rotas (app.py)
│   ├── agents/      # Triagem, síntese, validação (HITL)
│   ├── graph/        # Workflow LangGraph (state, nodes, tools, HITL)
│   ├── llm/            # Cliente do modelo (+ wrapper langchain-core), tradução PT-BR ↔ EN
│   ├── rag/             # Retriever + scripts de indexação ChromaDB
│   ├── logging/           # Auditoria (SQLite) e dashboard
│   ├── docs/               # Geração de documentos médicos (PDF)
│   └── data/                # Pipeline de dados + base estruturada de prontuários (SQLite)
├── pyproject.toml
├── requirements.txt
└── validate_backend.py    # Smoke test manual da API
```

## Instalação e execução
Pré-requisito importante: Recomendamos o uso do Python 3.11 ou 3.12. Versões muito recentes (como 3.14+) podem não ter suporte imediato das bibliotecas pesadas de Inteligência Artificial (como o PyTorch), causando erros na instalação.

```bash
cd backend
python -m venv venv
# No Windows: .\venv\Scripts\activate
# No Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
```

A API sobe em http://127.0.0.1:8000. O frontend (../frontend) espera a API rodando localmente nas portas padrão do CORS configurado em src/api/app.py.

Importante: pip install torch sozinho instala a build CPU-only por padrão mesmo em máquina com GPU — instale o torch com a build CUDA correta antes deste ```pip install -r requirements.txt``` (veja o comentário no próprio requirements.txt).

Rodando o Modelo Real vs. Mock
Sem LLM_MOCK=1 no ambiente, a API tenta carregar o BioMistral-7B + adapter LoRA de verdade (via transformers/peft) na primeira consulta — isso baixa e carrega um modelo de 7B parâmetros. Requer GPU com VRAM suficiente (ideal: 4-bit, ~5GB) ou bastante RAM em CPU (~28GB em fp32). Para desenvolvimento/teste sem GPU, mantenha LLM_MOCK=1 (é o padrão definido no startup da API).

Nota sobre Fallback de Memória: Caso a sua máquina não possua VRAM suficiente para suportar o modelo, a API fará uma "degradação elegante". Em vez de travar o sistema com um erro de Out of Memory, a IA retornará uma resposta no modo fallback indicando a indisponibilidade do LLM para que o fluxo não seja interrompido.

Comandos de Execução para Windows:
Para garantir que a aplicação não use o mock e ative o modelo real, passe a variável de ambiente corretamente de acordo com o seu terminal:

Se estiver usando Prompt de Comando (CMD):

DOS
```set LLM_MOCK=0 && python -m uvicorn src.api.app:app --reload --port 8000```

Se estiver usando PowerShell:

PowerShell
```$env:LLM_MOCK="0"```
```python -m uvicorn src.api.app:app --reload --port 8000```

### Fluxo de consulta (HITL em 2 etapas)

A consulta é dividida em duas chamadas — nenhum documento é gerado sem a decisão de um médico:

1. `POST /api/consulta` — roda o grafo (triagem → contexto do paciente → RAG → síntese → validação) e **pausa** no nó `hitl` (via `interrupt()` do LangGraph). Devolve `status: "aguardando_validacao"`, sem `documento`.
2. `POST /api/consulta/{session_id}/decisao` — body `{"decisao": "aprovado"|"editado"|"rejeitado", "texto_editado": "..."}`. Retoma o grafo a partir de onde parou; o documento só é gerado se a decisão for `aprovado` ou `editado`.

O estado pausado é persistido em `data/processed/checkpoints.db` (checkpointer SQLite do LangGraph), então sobrevive entre as duas requisições HTTP mesmo em processos/reloads diferentes.

## Variáveis de ambiente

| Variável | Default | Efeito |
|---|---|---|
| `LLM_MOCK` | `1` (definido automaticamente no `startup_event` da API se não estiver setado) | `1`/`true` → respostas sintéticas, sem GPU nem download de modelo. `0` → carrega o BioMistral-7B + adapter LoRA de verdade. |
| `LLM_MODEL` | `michelleAnogueira/biomistral-medquad-lora` | Repo do HuggingFace Hub (ou caminho local) do adapter LoRA fine-tunado a ser carregado. |
| `LLM_BASE_MODEL` | `BioMistral/BioMistral-7B` | Modelo base sobre o qual o adapter LoRA é aplicado (usado só se `LLM_MOCK=0`). |

Para rodar com um adapter novo (ex.: depois de um fine-tuning): `export LLM_MODEL=usuario/novo-adapter` (ou `set` no Windows) antes de subir a API com `LLM_MOCK=0`.

## Gerar os dados que o backend consome

- **Base de prontuários** (`data/processed/prontuarios.db`): **não precisa gerar nada manualmente** — `ProntuarioStore` cria e popula o banco sozinho (4 pacientes sintéticos) na primeira vez que qualquer coisa importa `src.data.prontuarios`.
- **Índice RAG** (`data/processed/chroma_index/`): a collection `chatbulario` (~68k bulas PT-BR, a única usada em produção hoje) é gerada com:
  ```bash
  cd backend
  python src/rag/build_index_chatbulario.py
  ```
  As collections `cid10` e `synthetic` (também consultadas pelo `Retriever`) hoje só existem via `src/rag/build_index_local.py` — que tem um caminho (`BASE`) hardcoded de outra máquina e monta uma collection `anvisa` obsoleta em vez de `chatbulario`. Precisa de ajuste antes de rodar; ver `data/README.md` e o `.gitignore` para os datasets brutos esperados (`cid10_subcategorias.csv`, `synthetic_clinical_notes_anonimizado.jsonl` — este último gerado por `python src/data/04_anonimizar_synthetic.py`).
- Sem o índice gerado, a API continua funcionando (RAG fica vazio, ver `Retriever` em `src/rag/retriever.py`) — só não traz contexto de bulário nas respostas.

## Smoke test

```bash
cd backend
python validate_backend.py
```

## Testes unitários

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

Os testes rodam em `LLM_MOCK=1` (definido automaticamente em `tests/conftest.py`), então não precisam de GPU nem baixam modelos.
