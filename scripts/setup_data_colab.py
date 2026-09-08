"""
Setup automático de dados no Google Colab.
Baixa todos os datasets públicos e reindexa no ChromaDB.

Uso (no Colab):
    !python scripts/setup_data_colab.py

Tempo: ~10-15 min
"""

import os
import json
import urllib.request
import zipfile
import io
import time
import pandas as pd
from pathlib import Path

# Tenta importar (vai falhar se não tiver)
try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
except ImportError:
    print("❌ chromadb não instalado. Rode:")
    print("   !pip install -q 'chromadb==0.4.18' 'pydantic==1.10.13' 'numpy<2.0'")
    raise

# ============================================================
# CONFIGURAÇÃO
# ============================================================
BASE_DIR = Path("/content/Techchalleng3")
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
CHROMA_DIR = DATA_DIR / "processed" / "chroma_index"
BATCH_SIZE_EMBEDDING = 1000

# Cria pastas
RAW_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)


def log(msg):
    """Print com timestamp."""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def download(url: str, dest: Path, timeout: int = 30) -> bool:
    """Baixa arquivo de URL."""
    try:
        log(f"📥 Baixando {url[:80]}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read()
        with open(dest, "wb") as f:
            f.write(data)
        size_kb = len(data) / 1024
        log(f"   ✅ Salvo: {dest.name} ({size_kb:.1f} KB)")
        return True
    except Exception as e:
        log(f"   ❌ Falhou: {e}")
        return False


# ============================================================
# 1. MEDQUAD
# ============================================================
log("=" * 70)
log("📚 [1/4] MedQuAD (NIH)")
log("=" * 70)

MEDQUAD_URL = "https://github.com/abachaa/MedQuAD/raw/master/medquad.csv"
MEDQUAD_FILE = RAW_DIR / "medquad_finetuning.jsonl"

if MEDQUAD_FILE.exists():
    log(f"⏭️  Já existe: {MEDQUAD_FILE.name}")
else:
    log("📥 Baixando MedQuAD do GitHub oficial...")
    try:
        import requests
        response = requests.get(MEDQUAD_URL, timeout=60)
        if response.status_code == 200:
            # Salva como JSONL (formato esperado pelo projeto)
            import csv
            import io as iom
            csv_data = response.content.decode("utf-8")
            reader = csv.DictReader(iom.StringIO(csv_data))

            with open(MEDQUAD_FILE, "w", encoding="utf-8") as f:
                count = 0
                for row in reader:
                    # Converte para formato Alpaca-like esperado
                    instruction = row.get("Question", "")
                    answer = row.get("Answer", "")
                    if instruction and answer:
                        json.dump({
                            "instruction": instruction,
                            "input": "",
                            "output": answer,
                        }, f, ensure_ascii=False)
                        f.write("\n")
                        count += 1
            log(f"✅ MedQuAD salvo: {MEDQUAD_FILE.name} ({count:,} amostras)")
    except Exception as e:
        log(f"⚠️  Erro MedQuAD: {e}")
        log("   Você pode baixar manualmente de https://github.com/abachaa/MedQuAD")


# ============================================================
# 2. CHATBULÁRIO
# ============================================================
log("=" * 70)
log("📚 [2/4] ChatBulário (HuggingFace)")
log("=" * 70)

try:
    from datasets import load_dataset

    log("📥 Baixando ChatBulário do HuggingFace...")
    ds = load_dataset("walmeidadf/ChatBulario", cache_dir=str(RAW_DIR))

    # Salva como JSONL
    for split_name in ["train", "validation", "test"]:
        out_path = RAW_DIR / f"chatbulario_{split_name}.jsonl"
        if out_path.exists():
            log(f"⏭️  Já existe: {out_path.name}")
            continue

        with open(out_path, "w", encoding="utf-8") as f:
            count = 0
            for sample in ds[split_name]:
                json.dump(sample, f, ensure_ascii=False)
                f.write("\n")
                count += 1
        log(f"✅ {split_name}: {count:,} amostras")

except Exception as e:
    log(f"❌ Erro ChatBulário: {e}")


# ============================================================
# 3. CID-10
# ============================================================
log("=" * 70)
log("📚 [3/4] CID-10 (DATASUS público)")
log("=" * 70)

CID10_FILE = RAW_DIR / "cid10_subcategorias.csv"

if CID10_FILE.exists():
    log(f"⏭️  Já existe: {CID10_FILE.name}")
else:
    # Tenta várias URLs públicas
    URLS = [
        "https://raw.githubusercontent.com/cleytonferrari/CidDataSus/master/CIDImport/Repositorio/Resources/CID-10-CAPITULOS.CSV",
        "https://raw.githubusercontent.com/cleytonferrari/CidDataSus/master/CIDImport/Repositorio/Resources/CID10CSV.csv",
    ]

    downloaded = False
    for url in URLS:
        if download(url, CID10_FILE):
            downloaded = True
            break

    if not downloaded:
        log("⚠️  URLs falharam. Criando CID-10 mínimo (100 doenças)...")
        cid10_min = [
            ("I21", "Infarto Agudo do Miocárdio"),
            ("I20", "Angina Instável"),
            ("I10", "Hipertensão Essencial"),
            ("E11", "Diabetes Mellitus Tipo 2"),
            ("E10", "Diabetes Mellitus Tipo 1"),
            ("J18", "Pneumonia"),
            ("J45", "Asma"),
            ("F32", "Episódio Depressivo"),
            ("F41", "Transtorno de Ansiedade"),
            ("M54", "Dorsalgia"),
            ("R51", "Cefaleia"),
            ("J44", "DPOC"),
            ("I50", "Insuficiência Cardíaca"),
            ("K21", "Doença de Refluxo Gastroesofágico"),
            ("J30", "Rinite Alérgica"),
            ("L20", "Dermatite Atópica"),
            ("E66", "Obesidade"),
            ("E78", "Dislipidemia"),
            ("I25", "Doença Isquêmica Crônica do Coração"),
            ("G43", "Enxaqueca"),
            ("M79", "Outros Transtornos dos Tecidos Moles"),
            ("R10", "Dor Abdominal e Pélvica"),
            ("F17", "Dependência de Nicotina"),
            ("K29", "Gastrite e Duodenite"),
            ("N39", "Outros Transtornos do Sistema Urinário"),
            ("I48", "Fibrilação e Flutter Atrial"),
            ("I63", "Infarto Cerebral"),
            ("H40", "Glaucoma"),
            ("H66", "Otite Média"),
            ("J03", "Amigdalite Aguda"),
            ("J06", "Infecção Aguda das Vias Aéreas Superiores"),
            ("K59", "Outros Transtornos Funcionais do Intestino"),
            ("M06", "Outras Artrites Reumatoides"),
            ("M17", "Gonartrose"),
            ("M81", "Osteoporose"),
            ("N18", "Insuficiência Renal Crônica"),
            ("N40", "Hiperplasia da Próstata"),
            ("R05", "Tosse"),
            ("R11", "Náusea e Vômito"),
            ("R53", "Mal-estar, Fadiga"),
            ("Z00", "Exame Geral"),
            ("A09", "Diarréia e Gastroenterite Infecciosa"),
            ("B34", "Infecção Viral NE"),
            ("D50", "Anemia por Deficiência de Ferro"),
            ("E03", "Hipotireoidismo"),
            ("E14", "Diabetes Mellitus NE"),
            ("E87", "Transtornos do Equilíbrio Hidroeletrolítico"),
            ("F10", "Transtornos Devidos ao Uso de Álcool"),
            ("F20", "Esquizofrenia"),
            ("F31", "Transtorno Afetivo Bipolar"),
            ("F43", "Reação ao Estresse Grave"),
            ("G40", "Epilepsia"),
            ("G44", "Outras Síndromes de Cefaleia"),
            ("G47", "Distúrbios do Sono"),
            ("H10", "Conjuntivite"),
            ("H25", "Catarata Senil"),
            ("H52", "Transtornos da Refração"),
            ("I80", "Trombose Venosa"),
            ("I83", "Varizes dos Membros Inferiores"),
            ("J00", "Nasofaringite Aguda"),
            ("J02", "Faringite Aguda"),
            ("J10", "Influenza"),
            ("J11", "Influenza com Vírus NE"),
            ("J15", "Pneumonia Bacteriana"),
            ("J20", "Bronquite Aguda"),
            ("K20", "Esofagite"),
            ("K35", "Apendicite Aguda"),
            ("K52", "Gastroenterites e Colites Não Infecciosas"),
            ("K76", "Outras Doenças do Fígado"),
            ("L23", "Dermatite Alérgica de Contato"),
            ("L40", "Psoríase"),
            ("L50", "Urticária"),
            ("M10", "Gota"),
            ("M13", "Outras Artrites"),
            ("M19", "Outras Artroses"),
            ("M25", "Outros Transtornos Articulares"),
            ("N20", "Calculose do Rim"),
            ("N80", "Endometriose"),
            ("O80", "Parto Único Espontâneo"),
            ("R07", "Dor de Garganta e Dor Torácica"),
            ("S06", "Traumatismo Intracraniano"),
            ("S52", "Fratura do Antebraço"),
            ("S72", "Fratura do Fêmur"),
            ("S82", "Fratura da Perna"),
            ("T78", "Efeitos Adversos NE"),
            ("Z23", "Necessidade de Imunização"),
            ("Z29", "Necessidade de Medidas Profiláticas"),
            ("Z51", "Outros Cuidados Médicos"),
            ("C50", "Neoplasia Maligna da Mama"),
            ("C61", "Neoplasia Maligna da Próstata"),
            ("C80", "Neoplasia Maligna NE"),
            ("D64", "Outras Anemias"),
            ("K59", "Síndrome do Intestino Irritável"),
            ("S52", "Fratura do Rádio e Ulna"),
            ("Z51", "Radioterapia"),
            ("A15", "Tuberculose Respiratória"),
            ("A41", "Outras Septicemias"),
            ("B19", "Hepatite Viral NE"),
            ("F33", "Transtorno Depressivo Recorrente"),
            ("G47", "Parassonias"),
            ("H10", "Conjuntivite Aguda"),
            ("I50", "Insuficiência Cardíaca Congestiva"),
            ("J18", "Broncopneumonia NE"),
            ("K29", "Gastrite e Duodenite"),
            ("M19", "Artrose do Joelho"),
            ("N18", "Doença Renal Crônica"),
            ("R10", "Dor Abdominal"),
            ("R50", "Cefaleia"),
            ("Z00", "Exame Médico Geral"),
        ]

        df_min = pd.DataFrame(cid10_min, columns=["SUBCAT", "DESCRICAO"])
        df_min.to_csv(CID10_FILE, sep=";", index=False, encoding="latin1")
        log(f"   ✅ CID-10 mínimo criado: {len(cid10_min)} códigos")


# ============================================================
# 4. SYNTHETIC CLINICAL NOTES
# ============================================================
log("=" * 70)
log("📚 [4/4] Synthetic Clinical Notes (HuggingFace)")
log("=" * 70)

SYNTH_FILE = RAW_DIR / "synthetic_clinical_notes" / "synthetic_clinical_notes.jsonl"

if SYNTH_FILE.exists() or (RAW_DIR / "synthetic_clinical_notes_anonimizado.jsonl").exists():
    log(f"⏭️  Já existe")
else:
    try:
        from datasets import load_dataset

        log("📥 Baixando Synthetic Notes do HuggingFace...")
        ds = load_dataset(
            "TonicAI/synthetic_clinical_notes",
            split="train",
            streaming=True,
            trust_remote_code=True,
        )

        SYNTH_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SYNTH_FILE, "w", encoding="utf-8") as f:
            count = 0
            for sample in ds:
                if count >= 3500:
                    break
                json.dump(sample, f, ensure_ascii=False)
                f.write("\n")
                count += 1
                if count % 500 == 0:
                    log(f"   Baixados: {count}")
        log(f"✅ Synthetic Notes: {count} notas")
    except Exception as e:
        log(f"❌ Erro Synthetic Notes: {e}")


# ============================================================
# RESUMO
# ============================================================
log("=" * 70)
log("📊 RESUMO DOS DATASETS")
log("=" * 70)

for f in sorted(RAW_DIR.glob("*")):
    if f.is_file():
        size_kb = f.stat().st_size / 1024
        log(f"   📄 {f.name:<40} ({size_kb:>8.1f} KB)")
    elif f.is_dir():
        sub_files = list(f.glob("*.jsonl")) + list(f.glob("*.csv"))
        if sub_files:
            total = sum(sf.stat().st_size for sf in sub_files) / 1024
            log(f"   📁 {f.name}/ ({len(sub_files)} arquivos, {total:.1f} KB)")


log("")
log("✅ SETUP COMPLETO!")
log("")
log("📋 Próximos passos:")
log("   1. Indexar tudo no ChromaDB:")
log("      python src/rag/build_index_chatbulario.py 10000")
log("   2. Carregar LLM:")
log("      (depois de copiar o modelo do Drive)")
log("   3. Subir UI:")
log("      python src/ui/gradio_app.py")
