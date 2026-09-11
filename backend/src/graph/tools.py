"""Tools do langchain-core usadas pelo grafo.

Uso:
    from src.graph.tools import consultar_prontuario
    resultado = consultar_prontuario.invoke({"paciente_id": "PAC-0001"})
"""

from __future__ import annotations

from langchain_core.tools import tool

from src.data.prontuarios import ProntuarioStore

_store = ProntuarioStore()


@tool
def consultar_prontuario(paciente_id: str) -> dict:
    """Consulta o histórico clínico estruturado de um paciente pelo ID (ex: PAC-0001).

    Retorna nome, idade, sexo, alergias, condições crônicas e histórico de
    consultas anteriores (data, motivo, diagnóstico, medicações). Se o
    paciente não for encontrado, retorna um dicionário vazio.
    """
    resultado = _store.buscar_por_id(paciente_id)
    return resultado or {}
