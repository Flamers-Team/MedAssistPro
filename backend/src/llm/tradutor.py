"""
Tradução PT-BR <-> EN com MarianMT (Helsinki-NLP).

Sem unsloth. Só usa `transformers` (MarianMTModel/MarianTokenizer). Serve para
adaptar a LLM (fine-tunada em inglês, no MedQuAD) a relatos/perguntas em
português na interface web.

Robustez: se os modelos não carregarem, os métodos viram *passthrough*
(retornam o texto original) e a UI continua funcionando em inglês.

Uso:
    from src.llm.tradutor import get_tradutor
    tr = get_tradutor()
    en = tr.pt_para_en("Paciente com dor torácica há 2 horas")
    pt = tr.en_para_pt("The patient likely has acute coronary syndrome")
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

MODEL_PT_EN = "Helsinki-NLP/opus-mt-tc-big-pt-en"
MODEL_EN_PT = "Helsinki-NLP/opus-mt-tc-big-en-pt"


class Tradutor:
    """Tradução bidirecional PT-BR <-> EN (MarianMT), com fallback passthrough."""

    def __init__(self, device: Optional[str] = None):
        self.ok = False
        self.device = device or "cpu"
        self._models: Dict[str, Tuple[object, object]] = {}

        try:
            import torch
            from transformers import MarianMTModel, MarianTokenizer

            self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
            for key, name in (("pt_en", MODEL_PT_EN), ("en_pt", MODEL_EN_PT)):
                tok = MarianTokenizer.from_pretrained(name)
                mdl = MarianMTModel.from_pretrained(name).to(self.device).eval()
                self._models[key] = (tok, mdl)
            self.ok = True
            print(f"Tradutor PT-BR carregado ({self.device}).")
        except Exception as e:  # noqa: BLE001
            print(f"Tradutor indisponivel - UI segue em ingles. Motivo: {e}")

    # ------------------------------------------------------------------
    def _translate(self, texto: str, key: str) -> str:
        if not self.ok or not isinstance(texto, str) or not texto.strip():
            return texto

        import torch

        tok, mdl = self._models[key]
        linhas = texto.split("\n")
        saida = []
        try:
            for linha in linhas:
                if not linha.strip():
                    saida.append(linha)
                    continue
                enc = tok(
                    [linha], return_tensors="pt", truncation=True, max_length=512
                ).to(self.device)
                with torch.no_grad():
                    gen = mdl.generate(
                        **enc, max_length=512, num_beams=2, early_stopping=True
                    )
                saida.append(tok.decode(gen[0], skip_special_tokens=True).strip())
            return "\n".join(saida)
        except Exception as e:  # noqa: BLE001
            print(f"Falha ao traduzir ({key}): {e}")
            return texto

    def pt_para_en(self, texto: str) -> str:
        return self._translate(texto, "pt_en")

    def en_para_pt(self, texto: str) -> str:
        return self._translate(texto, "en_pt")


# ============================================================
# SINGLETON
# ============================================================
_tradutor_singleton: Optional[Tradutor] = None


def get_tradutor() -> Tradutor:
    global _tradutor_singleton
    if _tradutor_singleton is None:
        _tradutor_singleton = Tradutor()
    return _tradutor_singleton


if __name__ == "__main__":
    tr = get_tradutor()
    print("PT->EN:", tr.pt_para_en("Paciente relata dor de cabeça intensa há 3 dias."))
    print("EN->PT:", tr.en_para_pt("The patient should undergo a complete blood count."))
