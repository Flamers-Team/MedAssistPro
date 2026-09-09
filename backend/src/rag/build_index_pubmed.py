"""
Indexa o dataset PubMed do NCBI no ChromaDB.

Usa o dataset `ncbi/pubmed` do HuggingFace (~35 milhões de abstracts médicos).
Para o Tech Challenge, indexamos uma AMOSTRA (10k-50k artigos) pra ser viável.

Diferença para o pmc/open_access:
- ncbi/pubmed: ~35M abstracts (sem texto completo, só abstract) - MAIS LEVE
- pmc/open_access: ~3.4M artigos com texto completo - MAIS PESADO

Para Tech Challenge, abstracts são suficientes porque:
- São menores (~300 chars vs 5000+)
- Já contêm info clínica essencial
- Indexam muito mais rápido

Uso:
    # Indexa 10k abstracts (~3 min)
    python src/rag/build_index_pubmed.py 10000

    # Indexa 50k abstracts (~15 min)
    python src/rag/build_index_pubmed.py 50000
"""

import json
import os
from pathlib import Path
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import time

# Desabilita telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Paths
BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
CHROMA_DIR = DATA_DIR / "processed" / "chroma_index"
PUBMED_COLLECTION = "pubmed"


def carregar_pubmed(limite: int = None) -> List[Dict]:
    """Carrega abstracts do PubMed via HuggingFace.

    Args:
        limite: número máximo de artigos (None = todos ~35M)
    """
    print(f"📥 Baixando PubMed do HuggingFace...")
    print(f"   Fonte: ncbi/pubmed")
    print(f"   Limite: {limite if limite else 'TODOS (~35M)'}")

    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError("Instale: pip install datasets")

    # Carrega dataset em streaming (não baixa tudo de uma vez)
    ds = load_dataset(
        "ncbi/pubmed",
        split="train",
        streaming=True,
        cache_dir=str(RAW_DIR),
        trust_remote_code=False,  # Esse dataset não precisa de trust_remote_code
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
    """Converte abstract PubMed em documento ChromaDB."""
    pmid = sample.get("MedlineID", sample.get("PMID", ""))
    title = sample.get("Title", "")
    abstract = sample.get("Abstract", "")
    # Alguns campos extras se existirem
    mesh_terms = sample.get("MeshTerms", [])
    authors = sample.get("Authors", [])

    # Monta documento embedável
    documento = f"""PMID: {pmid}
Title: {title}

Abstract:
{abstract}"""

    # Metadata filtrável
    metadata = {
        "pmid": str(pmid)[:50],
        "title": str(title)[:300],
        "abstract": str(abstract)[:500],
        "source": f"PubMed-{pmid}",
        "rag_source": "pubmed",
    }

    return {
        "id": f"pubmed-{pmid}",
        "document": documento,
        "metadata": metadata,
    }


def indexar_pubmed(limite: int = 10000):
    """Indexa PubMed no ChromaDB.

    Args:
        limite: número máximo de abstracts (None = todos, mas NÃO recomendado)
    """
    print("=" * 70)
    print("📚 INDEXAÇÃO DO PUBMED NO CHROMADB")
    print("=" * 70)

    # 1. Baixa abstracts
    samples = carregar_pubmed(limite)
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
        client.delete_collection(name=PUBMED_COLLECTION)
        print(f"🗑️  Collection '{PUBMED_COLLECTION}' antiga removida")
    except Exception:
        pass

    # 4. Cria nova collection
    print(f"\n📦 Criando collection '{PUBMED_COLLECTION}'...")
    collection = client.create_collection(
        name=PUBMED_COLLECTION,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    # 5. Indexa em batches
    BATCH_SIZE = 2000
    total = len(samples)
    start_time = time.time()

    print(f"\n⏳ Indexando {total:,} abstracts (batch={BATCH_SIZE})...")
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
    print(f"   Collection: '{PUBMED_COLLECTION}'")
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
            title = meta.get("title", "")[:80]
            dist = results["distances"][0][j-1] if "distances" in results else 0
            print(f"   [{j}] PMID:{pmid} - dist={dist:.3f}")
            print(f"       {title}...")


if __name__ == "__main__":
    import sys
    # Permite passar limite via CLI: python build_index_pubmed.py 10000
    limite = int(sys.argv[1]) if len(sys.argv) > 1 else 10000  # Default: 10k
    indexar_pubmed(limite=limite)
