"""
Indexa o dataset PMC Open Access no ChromaDB.

Usa o dataset `pmc/open_access` do HuggingFace (~3.4M artigos médicos).
Para o Tech Challenge, indexamos uma AMOSTRA (10k-50k artigos) pra ser viável.

Por que NÃO usar bulk download (FTP):
- ~50 GB de download (muito pesado)
- ~1-2 dias pra processar
- Não cabe no projeto

Por que usar o `pmc/open_access` do HuggingFace:
- Já vem parseado (text + metadata)
- Carrega via load_dataset (fácil)
- Licença aberta (Creative Commons)
- Amostragem controlada (escolhemos quantos indexar)

Uso:
    # Indexa 10k artigos (~5 min, suficiente pra demo)
    python src/rag/build_index_pmc.py 10000

    # Indexa 50k artigos (~20 min, produção leve)
    python src/rag/build_index_pmc.py 50000

    # Indexa TODOS (vai demorar HORAS, não recomendado)
    python src/rag/build_index_pmc.py
"""

import json
import os
from pathlib import Path
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import time
import random

# Desabilita telemetry do ChromaDB
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Paths
BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
CHROMA_DIR = DATA_DIR / "processed" / "chroma_index"
PMC_COLLECTION = "pmc"


def carregar_pmc(limite: int = None) -> List[Dict]:
    """Carrega artigos do PMC Open Access via HuggingFace.

    Args:
        limite: número máximo de artigos (None = todos)
    """
    print(f"📥 Baixando PMC Open Access do HuggingFace...")
    print(f"   Fonte: pmc/open_access")
    print(f"   Limite: {limite if limite else 'TODOS (~3.4M)'}")

    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError("Instale: pip install datasets")

    # Carrega dataset (streaming pra não baixar tudo de uma vez)
    # trust_remote_code=True porque o dataset tem script customizado
    ds = load_dataset(
        "pmc/open_access",
        split="train",
        streaming=True,
        cache_dir=str(RAW_DIR),
        trust_remote_code=True,
    )

    samples = []
    for i, sample in enumerate(ds):
        if limite and i >= limite:
            break
        samples.append(sample)
        if (i + 1) % 1000 == 0:
            print(f"   Baixados: {i+1:,} artigos")

    print(f"✅ Total baixado: {len(samples):,} artigos")
    return samples


def preparar_documento(sample: Dict) -> Dict:
    """Converte artigo PMC em documento ChromaDB."""
    pmid = sample.get("pmid", "")
    accession_id = sample.get("accession_id", "")

    # Texto principal: abstract + início do body (chunking pra não estourar limite)
    text = sample.get("text", "")
    abstract = sample.get("citation", "")

    # Pega só primeiros 2000 chars (chunking real pode ser feito depois)
    text_chunk = text[:2000] if text else ""

    # Monta documento embedável
    documento = f"""PMID: {pmid}
Accession ID: {accession_id}
Citation: {abstract}

Full Text:
{text_chunk}"""

    metadata = {
        "pmid": str(pmid)[:50],
        "accession_id": str(accession_id)[:50],
        "citation": str(abstract)[:300],
        "license": str(sample.get("license", ""))[:50],
        "retracted": str(sample.get("retracted", ""))[:10],
        "source": f"PMC-{accession_id}",
        "rag_source": "pmc",
    }

    # ID único (pmc + hash do texto pra evitar duplicatas)
    doc_id = f"pmc-{accession_id}"

    return {
        "id": doc_id,
        "document": documento,
        "metadata": metadata,
    }


def indexar_pmc(limite: int = 10000):
    """Indexa PMC Open Access no ChromaDB.

    Args:
        limite: número máximo de artigos (None = todos, mas NÃO recomendado)
    """
    print("=" * 70)
    print("📚 INDEXAÇÃO DO PMC OPEN ACCESS NO CHROMADB")
    print("=" * 70)

    # 1. Baixa artigos
    samples = carregar_pmc(limite)
    if not samples:
        print("❌ Nenhum artigo baixado!")
        return

    # 2. Conecta ao ChromaDB
    print(f"\n🔌 Conectando ao ChromaDB em {CHROMA_DIR}...")
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )

    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        device="cpu",
    )

    # 3. Deleta collection antiga se existir
    try:
        client.delete_collection(name=PMC_COLLECTION)
        print(f"🗑️  Collection '{PMC_COLLECTION}' antiga removida")
    except Exception:
        pass

    # 4. Cria nova collection
    print(f"\n📦 Criando collection '{PMC_COLLECTION}'...")
    collection = client.create_collection(
        name=PMC_COLLECTION,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    # 5. Indexa em batches
    BATCH_SIZE = 500
    total = len(samples)
    start_time = time.time()

    print(f"\n⏳ Indexando {total:,} artigos (batch={BATCH_SIZE})...")
    for i in range(0, total, BATCH_SIZE):
        batch = samples[i:i + BATCH_SIZE]
        docs = [preparar_documento(s) for s in batch]

        collection.add(
            ids=[d["id"] for d in docs],
            documents=[d["document"] for d in docs],
            metadatas=[d["metadata"] for d in docs],
        )

        done = min(i + BATCH_SIZE, total)
        elapsed = time.time() - start_time
        rate = done / elapsed if elapsed > 0 else 0
        eta = (total - done) / rate if rate > 0 else 0
        print(
            f"   ✅ {done:>6,}/{total:,} "
            f"({done/total*100:>5.1f}%) "
            f"- {rate:.0f} docs/s "
            f"- ETA: {eta:.0f}s"
        )

    elapsed_total = time.time() - start_time
    print(f"\n🎉 Indexação completa em {elapsed_total:.0f}s ({total/elapsed_total:.0f} docs/s)")
    print(f"   Collection: '{PMC_COLLECTION}'")
    print(f"   Total de documentos: {collection.count():,}")

    # 6. Teste rápido
    print("\n" + "=" * 70)
    print("🧪 TESTE DE RETRIEVAL")
    print("=" * 70)

    queries_teste = [
        "treatment for lung cancer",
        "symptoms of diabetes mellitus",
        "mRNA vaccine mechanism",
        "cardiovascular disease prevention",
    ]

    for q in queries_teste:
        print(f"\n❓ Query: '{q}'")
        results = collection.query(query_texts=[q], n_results=3)
        for j, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0]), 1):
            pmid = meta.get("pmid", "?")
            acc_id = meta.get("accession_id", "?")
            citation = meta.get("citation", "")[:80]
            dist = results["distances"][0][j-1] if "distances" in results else 0
            print(f"   [{j}] PMID:{pmid} (PMC-{acc_id}) - dist={dist:.3f}")
            print(f"       {citation}...")


if __name__ == "__main__":
    import sys
    # Permite passar limite via CLI
    limite = int(sys.argv[1]) if len(sys.argv) > 1 else 10000  # Default: 10k
    indexar_pmc(limite=limite)
