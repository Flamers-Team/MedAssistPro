# Backend

API FastAPI do Assistente Médico IA (agentes, RAG, LangGraph, geração de documentos, auditoria).

## Estrutura

```
backend/
├── src/
│   ├── api/        # FastAPI app e rotas (app.py)
│   ├── agents/      # Triagem, síntese, validação (HITL)
│   ├── graph/        # Workflow LangGraph (state, nodes)
│   ├── llm/            # Cliente do modelo, tradução PT-BR ↔ EN
│   ├── rag/             # Retriever + scripts de indexação ChromaDB
│   ├── logging/           # Auditoria (SQLite) e dashboard
│   ├── docs/               # Geração de documentos médicos (PDF)
│   └── data/                # Scripts de pipeline de dados (anonimização, split, validação)
├── pyproject.toml
├── requirements.txt
└── validate_backend.py    # Smoke test manual da API
```

## Instalação e execução

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn src.api.app:app --reload --port 8000
```

A API sobe em `http://127.0.0.1:8000`. O frontend (`../frontend`) espera a API rodando localmente nas portas padrão do CORS configurado em `src/api/app.py`.

Sem `LLM_MOCK=1` no ambiente, a API tenta carregar o BioMistral-7B + adapter LoRA de verdade (via `transformers`/`peft`) na primeira consulta — isso baixa e carrega um modelo de 7B parâmetros. Requer GPU com VRAM suficiente (ideal: 4-bit, ~5GB) ou bastante RAM em CPU (~28GB em fp32). **Importante**: `pip install torch` sozinho instala a build CPU-only por padrão mesmo em máquina com GPU — instale o torch com a build CUDA correta antes deste `pip install -r requirements.txt` (veja o comentário no próprio `requirements.txt`). Para desenvolvimento/teste sem GPU, mantenha `LLM_MOCK=1` (é o padrão definido no startup da API).

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
