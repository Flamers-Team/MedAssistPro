"""
Wrapper do ChromaDB pra consultas RAG.

Usa o dataset ChatBulário (68k bulas em PT-BR) indexado em data/processed/chroma_index/chatbulario.
Substituiu o anvisa_medicamentos.csv original (que só tinha metadados).

Por que ChatBulário:
- Tem texto completo das bulas (não só metadados)
- Já vem em formato pergunta-resposta
- PT-BR nativo
- 9 seções padronizadas (RDC 47/2009)

IMPORTANTE: Nenhum dado mockado. Se uma busca falhar ou coleção
não existir, retorna erro claro (RuntimeError).

Uso:
    from src.rag.retriever import Retriever
    retriever = Retriever()
    chunks = retriever.retrieve_chatbulario("efeitos colaterais de paracetamol", k=4)
"""

from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import os

# Desabilita telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"


# Caminho padrão do ChromaDB (gerado por build_index_chatbulario.py)
DEFAULT_CHROMA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed" / "chroma_index"


class Retriever:
    """Wrapper que consulta vector stores (ChatBulário + CID-10 + Synthetic Notes)."""

    # Collections válidas neste projeto
    VALID_COLLECTIONS = ["chatbulario", "cid10", "synthetic"]

    def __init__(self, chroma_dir: Path = DEFAULT_CHROMA_DIR):
        self.chroma_dir = Path(chroma_dir)

        if not self.chroma_dir.exists():
            raise FileNotFoundError(
                f"ChromaDB não encontrado em {self.chroma_dir}. "
                "Rode primeiro: python src/rag/build_index_chatbulario.py"
            )

        try:
            self.client = chromadb.PersistentClient(
                path=str(self.chroma_dir),
                settings=Settings(anonymized_telemetry=False),
            )
        except Exception as e:
            raise RuntimeError(
                f"Falha ao conectar ao ChromaDB em {self.chroma_dir}: {e}"
            )

        # Função de embedding (mesma usada pra indexar)
        try:
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu",  # ou "cuda" se tiver GPU
            )
        except Exception as e:
            raise RuntimeError(
                f"Falha ao carregar modelo de embedding "
                f"('sentence-transformers/all-MiniLM-L6-v2'): {e}"
            )

        # Conectar às collections existentes
        self.collections = {}
        for nome in self.VALID_COLLECTIONS:
            try:
                self.collections[nome] = self.client.get_collection(
                    name=nome,
                    embedding_function=self.embedding_fn,
                )
                count = self.collections[nome].count()
                print(f"✅ Collection '{nome}' carregada: {count:,} docs")
            except Exception as e:
                # NÃO falha aqui — só avisa que essa collection não tá disponível
                print(f"⚠️  Collection '{nome}' não disponível: {e}")

    def retrieve_chatbulario(self, query: str, k: int = 4) -> List[Dict]:
        """Busca no ChatBulário (bulas completas em PT-BR).

        Raises:
            RuntimeError: se collection não existe ou query falha
        """
        return self._retrieve("chatbulario", query, k)

    # Mantido por retrocompatibilidade (alguns lugares ainda chamam retrieve_anvisa)
    def retrieve_anvisa(self, query: str, k: int = 4) -> List[Dict]:
        """Mantido por retrocompatibilidade - agora usa ChatBulário."""
        return self.retrieve_chatbulario(query, k)

    def retrieve_cid10(self, query: str, k: int = 4) -> List[Dict]:
        """Busca na base de códigos CID-10.

        Raises:
            RuntimeError: se collection não existe ou query falha
        """
        return self._retrieve("cid10", query, k)

    def retrieve_synthetic(self, query: str, k: int = 4) -> List[Dict]:
        """Busca nas notas clínicas sintéticas.

        Raises:
            RuntimeError: se collection não existe ou query falha
        """
        return self._retrieve("synthetic", query, k)

    def retrieve_interno(self, query: str, k: int = 4) -> List[Dict]:
        """Busca combinada na base interna (ChatBulário + CID-10 + Synthetic).

        Raises:
            RuntimeError: se nenhuma collection tá disponível
        """
        chunks = []
        errors = []

        # Distribuir k entre as 3 sources
        per_source = max(1, k // 3)
        for source in ["chatbulario", "cid10", "synthetic"]:
            try:
                chunks.extend(self._retrieve(source, query, per_source))
            except RuntimeError as e:
                errors.append(f"{source}: {e}")

        # Se nenhuma collection funcionou, falha
        if not chunks and errors:
            raise RuntimeError(
                f"Nenhuma collection RAG disponível. Erros: {'; '.join(errors)}"
            )

        return chunks[:k]

    def _retrieve(self, source: str, query: str, k: int) -> List[Dict]:
        """Retrieval genérico em uma collection.

        Raises:
            RuntimeError: se collection não existe ou query falha
        """
        if source not in self.collections:
            raise RuntimeError(
                f"Collection '{source}' não está carregada. "
                f"Verifique se foi indexada. Collections disponíveis: "
                f"{list(self.collections.keys())}"
            )

        if not query or not query.strip():
            raise ValueError("Query não pode ser vazia")

        try:
            results = self.collections[source].query(
                query_texts=[query],
                n_results=k,
            )
        except Exception as e:
            raise RuntimeError(
                f"Erro ao buscar '{query}' em '{source}': {e}"
            )

        # Verifica se retornou algo
        if not results.get("documents") or not results["documents"][0]:
            return []  # Busca sem resultados (NÃO é erro)

        chunks = []
        for i in range(len(results["documents"][0])):
            chunks.append({
                "source": results["metadatas"][0][i].get("source", source),
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "rag_source": source,
            })
        return chunks

    def formatar_contexto(self, chunks: List[Dict], max_chars: int = 3000) -> str:
        """Formata lista de chunks em texto único pro prompt do LLM."""
        if not chunks:
            return "(nenhum resultado encontrado no RAG)"

        contexto = ""
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("source", "?")
            content = chunk.get("content", "")[:500]
            contexto += f"\n[{i}] Fonte: {source}\n{content}\n"

            if len(contexto) > max_chars:
                contexto = contexto[:max_chars] + "..."
                break

        return contexto


# ============================================================
# TESTE
# ============================================================
if __name__ == "__main__":
    print("="*60)
    print("🔍 TESTANDO RETRIEVER (ChatBulário)")
    print("="*60)

    retriever = Retriever()

    # Testar retrieval
    print("\n--- CHATBULÁRIO (PT-BR, bulas completas) ---")
    resultados = retriever.retrieve_chatbulario("paracetamol adulto", k=3)
    for r in resultados:
        meta = r['metadata']
        print(f"   • {meta.get('nome_produto', '?')[:60]}")
        print(f"     Seção: {meta.get('secao_id', '?')} | {meta.get('classe_terapeutica', '')[:60]}")
        # Mostra primeiro pedaço da resposta
        content_lines = r['content'].split("\n")
        for line in content_lines:
            if line.startswith("Resposta:"):
                print(f"     {line[:100]}...")
                break

    print("\n--- INTERNO (combinado) ---")
    resultados = retriever.retrieve_interno("efeitos colaterais de AAS", k=4)
    for r in resultados:
        meta = r['metadata']
        nome = meta.get('nome_produto', meta.get('source', '?'))[:40]
        print(f"   • [{r['rag_source']}] {nome}")
