"""
Gradio App FINAL — Assistente Médico (Tech Challenge Fase 3)
=============================================================

Integra:
- LLM real (BioMistral fine-tuned) ou mock
- RAG (ChromaDB) com 3 vector stores
- Gerador de PDFs (ReportLab)
- Sistema de auditoria (SQLite)
- HITL (médico ratifica antes de gerar docs)

Uso:
    python src/ui/gradio_app.py
    # abre em http://127.0.0.1:7860
    # login: medico / demo123
"""

import json
import os
import sqlite3
import sys
import uuid
from datetime import datetime
from pathlib import Path

import gradio as gr

# Compatibilidade com gradio_client 1.x/4.x quando o schema usa bool em vez de dict.
try:
    from gradio_client import utils as gradio_client_utils

    def _safe_get_type(schema):
        if not isinstance(schema, dict):
            return {}
        if "const" in schema:
            return "const"
        if "enum" in schema:
            return "enum"
        if "type" in schema:
            return schema["type"]
        if schema.get("$ref"):
            return "$ref"
        if schema.get("oneOf"):
            return "oneOf"
        if schema.get("anyOf"):
            return "anyOf"
        if schema.get("allOf"):
            return "allOf"
        if "type" not in schema:
            return {}
        raise ValueError(f"Cannot parse type for {schema}")

    gradio_client_utils.get_type = _safe_get_type
except Exception:
    pass

# Adicionar raiz ao path pra imports funcionarem
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# ============================================================
# CONFIGURAÇÃO
# ============================================================
DB_PATH = Path("audit.db")
DOCS_DIR = Path("data/documents")
DOCS_DIR.mkdir(parents=True, exist_ok=True)

SESSION_ID = str(uuid.uuid4())[:8]
USER_ID = "dr.demonstracao"

# ============================================================
# PIPELINE COMPLETO (integra tudo)
# ============================================================
_tradutor = None  # tradutor PT-BR <-> EN (carregado sob demanda)


def inicializar_componentes():
    """Inicializa LLM + Retriever + DocGenerator + Tradutor (lazy loading)."""
    global _llm, _retriever, _doc_gen, _tradutor
    if "_llm" not in globals():
        from src.llm.client import get_llm
        from src.rag.retriever import Retriever
        from src.docs.generator import DocumentGenerator

        _llm = get_llm()
        try:
            _retriever = Retriever()
        except Exception as e:
            print(f"⚠️  Retriever não carregado: {e}")
            _retriever = None
        _doc_gen = DocumentGenerator(output_dir=str(DOCS_DIR))

        # Tradução PT-BR <-> EN (a LLM foi treinada em inglês).
        # Desliga com UI_TRANSLATE=0 ou em modo mock.
        _tradutor = None
        if (
            os.getenv("UI_TRANSLATE", "1").lower() in ("1", "true", "yes")
            and os.getenv("LLM_MOCK", "0").lower() not in ("1", "true", "yes")
        ):
            try:
                from src.llm.tradutor import get_tradutor

                _tradutor = get_tradutor()
            except Exception as e:  # noqa: BLE001
                print(f"⚠️  Tradutor não carregado: {e}")
                _tradutor = None


def _traduzir_triagem(tri: dict, tr) -> dict:
    """Traduz EN->PT os campos de texto livre da triagem."""
    if not isinstance(tri, dict) or tr is None or not getattr(tr, "ok", False):
        return tri
    out = dict(tri)
    if out.get("justificativa"):
        out["justificativa"] = tr.en_para_pt(out["justificativa"])
    return out


def _traduzir_sintese(s: dict, tr) -> dict:
    """Traduz EN->PT os campos de texto livre da síntese (mantém CID, doses, nomes)."""
    if not isinstance(s, dict) or tr is None or not getattr(tr, "ok", False):
        return s
    out = dict(s)
    if out.get("observacoes"):
        out["observacoes"] = tr.en_para_pt(out["observacoes"])
    out["hipoteses"] = [
        {**h, "justificativa": tr.en_para_pt(h["justificativa"])}
        if isinstance(h, dict) and h.get("justificativa")
        else h
        for h in out.get("hipoteses", [])
    ]
    out["exames_sugeridos"] = [
        {**e, "justificativa": tr.en_para_pt(e["justificativa"])}
        if isinstance(e, dict) and e.get("justificativa")
        else e
        for e in out.get("exames_sugeridos", [])
    ]
    return out


def processar_consulta(relato: str, nome_paciente: str, idade: str, sexo: str,
                       traduzir: bool = True, progress=gr.Progress()):
    """Pipeline completo: (tradução PT→EN) → LLM + RAG → síntese → validação → (tradução EN→PT)."""
    inicializar_componentes()

    usar_traducao = bool(traduzir) and _tradutor is not None and getattr(_tradutor, "ok", False)

    # A LLM foi treinada em inglês: traduz o relato PT→EN para os agentes.
    # O RAG continua usando o relato ORIGINAL (ChatBulário é PT-BR).
    relato_en = relato
    if usar_traducao:
        progress(0.05, desc="🌐 Traduzindo relato PT→EN...")
        relato_en = _tradutor.pt_para_en(relato)

    progress(0.1, desc="🔍 Etapa 1/5: Triagem clínica...")

    # Agente 1: Triagem (via src/agents/triagem.py)
    from src.agents.triagem import triar
    tri = triar(relato_en)
    log_event("triagem", agent="triagem", input_data=relato_en, output_data=tri)

    progress(0.3, desc="📚 Etapa 2/5: Buscando bulas (RAG ChatBulário)...")
    # RAG: usa apenas o ChatBulário (bulas PT-BR) — com o relato original em PT
    rag_pmc = []  # Mantido por compatibilidade com UI
    rag_interno = []
    if _retriever:
        try:
            rag_interno = _retriever.retrieve_interno(relato, k=5)
        except RuntimeError as e:
            print(f"⚠️  RAG falhou: {e}")
            # Segue sem RAG — LLM pode responder com conhecimento próprio
            rag_interno = []

    progress(0.7, desc="🧠 Etapa 4/5: Gerando síntese clínica...")
    # Agente 2: Síntese
    from src.agents.sintese import sintetizar
    sintese = sintetizar(relato_en, rag_pmc, rag_interno)
    log_event("sintese", agent="sintese", input_data=relato_en, output_data=sintese)

    progress(0.9, desc="✅ Etapa 4/4: Validando e formatando...")
    # Adicionar disclaimer
    sintese["disclaimer"] = (
        "⚕️ ATENÇÃO: Esta resposta foi gerada por IA e constitui APENAS "
        "uma sugestão. A validação do médico assistente é obrigatória "
        "antes de qualquer conduta clínica."
    )
    # Adicionar info da triagem
    sintese["triagem"] = tri

    # Agente 3: Validação
    from src.agents.validacao import validar
    validated = validar(sintese, tri, _llm)
    log_event("validacao", agent="validacao", input_data=sintese, output_data=validated)

    # Traduz de volta EN→PT os textos livres para exibição
    if usar_traducao:
        progress(0.95, desc="🌐 Traduzindo resposta EN→PT...")
        tri = _traduzir_triagem(tri, _tradutor)
        validated = _traduzir_sintese(validated, _tradutor)
        validated["triagem"] = tri

    progress(1.0, desc="✅ Concluído!")

    return tri, rag_pmc, rag_interno, validated


def finalizar_consulta(decisao: str, texto_editado: str, sintese_atual: dict,
                       nome: str, idade: str, sexo: str):
    """Processa decisão do HITL e gera PDFs reais com ReportLab."""
    inicializar_componentes()

    if decisao == "rejeitar":
        log_event("hitl_decision", action="rejeitado")
        return "❌ Consulta rejeitada. Nenhum documento gerado.", None, None, None

    log_event("hitl_decision", action=decisao, texto_editado=texto_editado)

    # Preparar dados pra ReportLab
    texto_final = texto_editado if (decisao == "editar" and texto_editado) else str(sintese_atual)

    dados_pdf = {
        "paciente": nome or "Não informado",
        "idade": idade or "—",
        "sexo": sexo or "—",
        "medico": "Dr(a). Responsável",
        "crm": "000000-DF",
        "queixa_principal": texto_final[:500] if texto_final else "",
        "exame_fisico": "Conforme avaliação clínica (ver prontuário anterior)",
        "hipoteses": sintese_atual.get("hipoteses", []),
        "exames_sugeridos": sintese_atual.get("exames_sugeridos", []),
        "medicacoes_sugeridas": sintese_atual.get("medicacoes_sugeridas", []),
        "observacoes": sintese_atual.get("observacoes", ""),
        "dias_afastamento": "7",
        "motivo": "condição clínica",
    }

    # Gerar PDFs REAIS
    prontuario = _doc_gen.gerar_prontuario(dados_pdf)
    atestado = _doc_gen.gerar_atestado(dados_pdf)
    receita = _doc_gen.gerar_receita(dados_pdf)
    log_event("document_generated", document_type="prontuario+atestado+receita")

    return (
        f"✅ Documentos PDF gerados com sucesso!",
        prontuario,
        atestado,
        receita,
    )


def log_event(event_type: str, **kwargs):
    """Grava evento no SQLite."""
    try:
        from src.logging.audit import init_db, log_event
        from src.logging.schemas import LLMCallEvent, HITLDecisionEvent, DocumentGeneratedEvent

        init_db()

        if event_type in ("triagem", "sintese", "validacao"):
            event = LLMCallEvent(
                event_type="llm_call",
                session_id=SESSION_ID,
                user_id=USER_ID,
                agent=kwargs.get("agent", event_type),
                input_preview=str(kwargs.get("input_data", ""))[:500],
                output_preview=str(kwargs.get("output_data", ""))[:500],
                tokens_in=len(str(kwargs.get("input_data", ""))) // 4,
                tokens_out=len(str(kwargs.get("output_data", ""))) // 4,
            )
        elif event_type == "hitl_decision":
            event = HITLDecisionEvent(
                event_type="hitl_decision",
                session_id=SESSION_ID,
                user_id=USER_ID,
                action=kwargs.get("action", ""),
                texto_original=str(kwargs.get("texto_editado", ""))[:500],
            )
        elif event_type == "document_generated":
            event = DocumentGeneratedEvent(
                event_type="document_generated",
                session_id=SESSION_ID,
                user_id=USER_ID,
                document_type=kwargs.get("document_type", ""),
                file_path="generated",
            )
        else:
            return

        log_event(event)
    except Exception as e:
        print(f"Erro ao logar: {e}")


# ============================================================
# DASHBOARD
# ============================================================
def get_audit_dashboard(horas: int = 24) -> tuple[str, str]:
    """Retorna texto do dashboard + métricas."""
    if not DB_PATH.exists():
        return "📊 Banco ainda não inicializado. Faça uma consulta primeiro.", "0"

    try:
        from src.logging.dashboard import dashboard_resumo
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            dashboard_resumo(horas=horas)

        conn = sqlite3.connect(str(DB_PATH))
        total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        sessoes = conn.execute("SELECT COUNT(DISTINCT session_id) FROM events").fetchone()[0]
        conn.close()

        return buf.getvalue(), f"**{total:,}** eventos | **{sessoes}** sessões"
    except Exception as e:
        return f"Erro: {e}", "0"


def listar_documentos() -> str:
    """Lista PDFs gerados."""
    if not DOCS_DIR.exists():
        return "Nenhum documento gerado ainda."

    docs = sorted(DOCS_DIR.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not docs:
        return "Nenhum documento gerado ainda."

    md = "📄 **Documentos PDF gerados (mais recentes primeiro):**\n\n"
    for doc in docs[:20]:
        mtime = datetime.fromtimestamp(doc.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        size_kb = doc.stat().st_size / 1024
        md += f"- 📄 `{doc.name}` ({size_kb:.1f} KB) — {mtime}\n"
    return md


# ============================================================
# UI GRADIO
# ============================================================
with gr.Blocks(
    title="🏥 Assistente Médico Inteligente",
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="cyan"),
) as demo:

    gr.Markdown(f"""
    # 🏥 Tech Challenge Fase 3 — Assistente Médico Inteligente

    **Sessão**: `{SESSION_ID}` | **Usuário**: `{USER_ID}` | **Status**: 🟢 Online

    Pipeline: Relato → Triagem → RAG (ChatBulário) → Síntese → HITL → PDFs
    """)

    sintese_state = gr.State({})

    with gr.Tabs():

        # ============================================================
        # ABA 1: CONSULTA
        # ============================================================
        with gr.Tab("📋 Consulta"):
            gr.Markdown("### 1️⃣ Dados do Paciente e Relato Inicial")

            with gr.Row():
                with gr.Column():
                    nome = gr.Textbox(label="👤 Nome do Paciente", placeholder="Maria Silva")
                with gr.Column():
                    idade = gr.Textbox(label="🎂 Idade", placeholder="45")
                with gr.Column():
                    sexo = gr.Radio(["Feminino", "Masculino", "Outro"], label="⚧ Sexo")

            relato = gr.Textbox(
                label="📝 Relato Clínico",
                placeholder="Ex: Paciente relata dor torácica em aperto há 3h, irradiando para braço esquerdo...",
                lines=5,
            )

            traduzir_chk = gr.Checkbox(
                label="🌐 Traduzir PT-BR ⇄ EN (recomendado — a LLM foi treinada em inglês)",
                value=True,
            )

            iniciar_btn = gr.Button("🚀 Iniciar Consulta", variant="primary", size="lg")
            gr.Markdown("---")

            gr.Markdown("### 2️⃣ Resultado do Pipeline")
            with gr.Row():
                with gr.Column():
                    triagem_out = gr.JSON(label="🚨 Triagem (Agente 1)")
                with gr.Column():
                    sintese_out = gr.JSON(label="🧠 Síntese (Agentes 2+3)")

            with gr.Row():
                with gr.Column():
                    rag_pmc_out = gr.JSON(label="📚 RAG Bulas (ChatBulário)")
                with gr.Column():
                    rag_interno_out = gr.JSON(label="🏥 RAG Base Interna")

            gr.Markdown("### 3️⃣ Decisão do Médico (HITL)")
            with gr.Row():
                aprovar_btn = gr.Button("✅ Aprovar como está", variant="primary")
                editar_btn = gr.Button("✏️ Editar texto", variant="secondary")
                rejeitar_btn = gr.Button("❌ Rejeitar", variant="stop")

            texto_editado = gr.Textbox(
                label="📝 Texto editado (se clicou em 'Editar')",
                lines=5,
                visible=False,
            )

            status_hitl = gr.Markdown("")
            gr.Markdown("### 4️⃣ Documentos PDF Gerados")
            with gr.Row():
                prontuario_file = gr.File(label="📄 Prontuário", visible=False)
                atestado_file = gr.File(label="📄 Atestado", visible=False)
                receita_file = gr.File(label="📄 Receita", visible=False)

            # Eventos
            def iniciar(rel, n, i, s, trad):
                tri, rpmc, rint, sint = processar_consulta(rel, n, i, s, traduzir=trad)
                return tri, rpmc, rint, sint, sint

            iniciar_btn.click(
                iniciar, inputs=[relato, nome, idade, sexo, traduzir_chk],
                outputs=[triagem_out, rag_pmc_out, rag_interno_out, sintese_out, sintese_state],
            )

            editar_btn.click(lambda: gr.update(visible=True), outputs=[texto_editado])

            def on_aprovar(s):
                return finalizar_consulta("aprovado", "", s, nome.value, idade.value, sexo.value)

            def on_editar(t, s):
                return finalizar_consulta("editar", t, s, nome.value, idade.value, sexo.value)

            def on_rejeitar(s):
                return finalizar_consulta("rejeitar", "", s, nome.value, idade.value, sexo.value)

            def show_files(p, a, r):
                return (
                    gr.update(value=p, visible=True) if p else gr.update(visible=False),
                    gr.update(value=a, visible=True) if a else gr.update(visible=False),
                    gr.update(value=r, visible=True) if r else gr.update(visible=False),
                )

            aprovar_btn.click(
                on_aprovar, inputs=[sintese_state],
                outputs=[status_hitl, prontuario_file, atestado_file, receita_file],
            )
            editar_btn.click(
                on_editar, inputs=[texto_editado, sintese_state],
                outputs=[status_hitl, prontuario_file, atestado_file, receita_file],
            )
            rejeitar_btn.click(
                on_rejeitar, inputs=[sintese_state],
                outputs=[status_hitl, prontuario_file, atestado_file, receita_file],
            )

        # ============================================================
        # ABA 2: AUDITORIA
        # ============================================================
        with gr.Tab("📊 Auditoria"):
            gr.Markdown("### Logs de Auditoria (SQLite)")
            with gr.Row():
                horas_slider = gr.Slider(1, 168, value=24, step=1, label="Período (horas)")
                refresh_btn = gr.Button("🔄 Atualizar")

            metricas_out = gr.Markdown("Carregando...")
            dashboard_out = gr.Textbox(label="Dashboard completo", lines=20, max_lines=30)

            def refresh_dash(h):
                dash, m = get_audit_dashboard(int(h))
                return m, dash

            refresh_btn.click(refresh_dash, inputs=[horas_slider], outputs=[metricas_out, dashboard_out])
            demo.load(refresh_dash, inputs=[horas_slider], outputs=[metricas_out, dashboard_out])

        # ============================================================
        # ABA 3: DOCUMENTOS
        # ============================================================
        with gr.Tab("📁 Documentos"):
            gr.Markdown("### PDFs Gerados")
            docs_out = gr.Markdown(listar_documentos())
            refresh_docs_btn = gr.Button("🔄 Atualizar Lista")
            refresh_docs_btn.click(lambda: listar_documentos(), outputs=[docs_out])

        # ============================================================
        # ABA 4: CONFIG
        # ============================================================
        with gr.Tab("⚙️ Config"):
            gr.Markdown(f"""
            ### Sistema

            | Item | Valor |
            |------|-------|
            | **LLM** | BioMistral-7B + LoRA (modo mock até treinar) |
            | **RAG** | ChromaDB: ANVISA (43k) + CID-10 (12k) + Synthetic (3k) |
            | **PDFs** | ReportLab (prontuário, atestado, receita, laudo) |
            | **Auditoria** | SQLite em `{DB_PATH}` |
            | **Sessão** | `{SESSION_ID}` |
            | **Diretório docs** | `{DOCS_DIR}` |

            **Stack**: LangChain + LangGraph + ChromaDB + ReportLab + SQLite + Gradio
            """)


# ============================================================
# LAUNCH
# ============================================================
if __name__ == "__main__":
    print("="*60)
    print("🏥 INICIANDO ASSISTENTE MÉDICO INTELIGENTE (VERSÃO FINAL)")
    print("="*60)

    # Tentar inicializar componentes
    try:
        inicializar_componentes()
        print("✅ Todos os componentes inicializados!")
    except Exception as e:
        print(f"⚠️  Erro na inicialização: {e}")
        print("   Continuando com fallbacks (modo demo)...")

    demo.launch(
        share=os.getenv("GRADIO_SHARE", "0").lower() in ("1", "true", "yes"),
        server_name="127.0.0.1",
        server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
        auth=("medico", "demo123"),
        show_error=True,
    )
    print("\n✅ Servidor rodando!")
    print("   Local:    http://127.0.0.1:7860")
    print("   Mobile:   http://<seu-IP>:7860")
    print("   Login:    medico / demo123")