import pytest

from src.data.prontuarios import ProntuarioStore


@pytest.fixture()
def store(tmp_path):
    return ProntuarioStore(db_path=tmp_path / "prontuarios_teste.db")


def test_seed_popula_pacientes_sinteticos(store):
    ids = store.listar_ids()
    assert "PAC-0001" in ids
    assert len(ids) >= 4


def test_buscar_por_id_retorna_estrutura_completa(store):
    p = store.buscar_por_id("PAC-0001")
    assert p["paciente_id"] == "PAC-0001"
    assert p["nome"]
    assert isinstance(p["historico"], list)
    assert isinstance(p["alergias"], list)


def test_buscar_por_id_inexistente_retorna_none(store):
    assert store.buscar_por_id("PAC-9999") is None


def test_buscar_por_id_vazio_retorna_none(store):
    assert store.buscar_por_id("") is None
    assert store.buscar_por_id(None) is None


def test_reabrir_store_nao_duplica_seed(tmp_path):
    db_path = tmp_path / "prontuarios_teste.db"
    ProntuarioStore(db_path=db_path)
    store2 = ProntuarioStore(db_path=db_path)
    assert len(store2.listar_ids()) == len(set(store2.listar_ids()))
