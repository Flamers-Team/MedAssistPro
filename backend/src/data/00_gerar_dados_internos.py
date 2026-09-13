"""
Gera o dataset de dados internos do hospital para o fine-tuning.

Os três tipos de conteúdo exigidos pelo enunciado (protocolos médicos do
hospital, perguntas frequentes de médicos e modelos de laudos, receitas e
procedimentos) são escritos nos módulos de `dados_internos/` e convertidos
aqui para o formato instruction/input/output, o mesmo do MedQuAD.

O prompt de cada exemplo reproduz exatamente o que os agentes montam em
produção (`src/agents/triagem.py` e `src/agents/sintese.py`), para o modelo
aprender a responder no formato que o sistema espera.

⚠️ Conteúdo sintético. Não é material institucional real e não passou por
validação clínica: a equipe não tem médico. Está declarado no relatório.

Uso:
    python src/data/00_gerar_dados_internos.py

Saída:
    data/raw/dados_internos_hospital.jsonl
"""

import json
import sys
from collections import Counter
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))

from src.agents.sintese import SINTESE_SYSTEM_PROMPT, _formatar_historico  # noqa: E402
from src.agents.triagem import TRIAGEM_SYSTEM_PROMPT  # noqa: E402
from src.data.dados_internos.duvidas import DUVIDAS  # noqa: E402
from src.data.dados_internos.modelos import MODELOS  # noqa: E402
from src.data.dados_internos.protocolos import PROTOCOLOS  # noqa: E402

PROJETO = BACKEND.parent
SAIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else PROJETO / "data" / "raw" / "dados_internos_hospital.jsonl"

ORIGEM = "sintetico-interno"


def _json(dados: dict) -> str:
    return json.dumps(dados, ensure_ascii=False, indent=2)


def exemplos_triagem() -> list[dict]:
    """Protocolos do hospital, no formato do agente de triagem."""
    return [
        {
            "instruction": f"{TRIAGEM_SYSTEM_PROMPT}\n\nRelato: {p['relato']}",
            "input": "",
            "output": _json(p["triagem"]),
            "tipo": "protocolo_triagem",
            "origem": ORIGEM,
        }
        for p in PROTOCOLOS
    ]


def exemplos_sintese() -> list[dict]:
    """Dúvidas de médicos, no formato do agente de síntese."""
    exemplos = []
    for d in DUVIDAS:
        contexto_interno = "\n".join(d["rag"]) or "(sem protocolos específicos)"
        user = f"""
RELATO: {d['relato']}

=== HISTÓRICO DO PACIENTE ===
{_formatar_historico(d.get('historico'))}

=== LITERATURA (PMC) ===
(sem resultados relevantes)

=== PROTOCOLOS INTERNOS ===
{contexto_interno}

Resposta JSON:"""
        exemplos.append({
            "instruction": f"{SINTESE_SYSTEM_PROMPT}\n\n{user}",
            "input": "",
            "output": _json(d["sintese"]),
            "tipo": "duvida_medico",
            "origem": ORIGEM,
        })
    return exemplos


def exemplos_documentos() -> list[dict]:
    """Modelos de laudo, receita e procedimentos internos."""
    return [
        {
            "instruction": m["pedido"],
            "input": "",
            "output": m["documento"],
            "tipo": "modelo_documento",
            "origem": ORIGEM,
        }
        for m in MODELOS
    ]


def main() -> None:
    exemplos = exemplos_triagem() + exemplos_sintese() + exemplos_documentos()

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", encoding="utf-8") as f:
        for e in exemplos:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    tipos = Counter(e["tipo"] for e in exemplos)
    tamanho = SAIDA.stat().st_size / 1024

    print("=" * 60)
    print("DATASET DE DADOS INTERNOS GERADO")
    print("=" * 60)
    print(f"Arquivo:  {SAIDA}")
    print(f"Tamanho:  {tamanho:.1f} KB")
    print(f"Exemplos: {len(exemplos)}")
    for tipo, n in tipos.items():
        print(f"  - {tipo}: {n}")
    print()
    print("Conteúdo sintético, sem validação clínica. Ver relatório técnico.")


if __name__ == "__main__":
    main()
