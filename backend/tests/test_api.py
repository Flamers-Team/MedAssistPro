def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_login_sucesso(client):
    resp = client.post("/api/auth/login", json={"username": "medico", "password": "demo123"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_login_falha_com_credenciais_erradas(client):
    resp = client.post("/api/auth/login", json={"username": "medico", "password": "senha-errada"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    assert "inválidas" in body["message"]


def test_login_rejeita_campos_vazios(client):
    resp = client.post("/api/auth/login", json={"username": "", "password": ""})
    assert resp.status_code == 422


def test_consulta_rejeita_relato_curto_demais(client):
    # min_length=10 no schema — string curta nem chega a rodar o handler
    resp = client.post("/api/consulta", json={"relato": "dor"})
    assert resp.status_code == 422


def test_consulta_rejeita_relato_em_branco(client):
    # passa no min_length=10 (so espacos), mas o handler valida apos o strip()
    resp = client.post("/api/consulta", json={"relato": " " * 10})
    assert resp.status_code == 400


def test_consulta_retorna_estrutura_completa(client):
    resp = client.post(
        "/api/consulta",
        json={
            "relato": "Paciente relata febre e tosse ha 3 dias, sem dispneia.",
            "paciente": {"nome": "Teste", "idade": "30", "sexo": "M"},
            "medico": {"nome": "Dr Teste", "crm": "11111"},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in ("ok", "partial")
    assert "session_id" in body
    assert "triagem" in body and "categoria" in body["triagem"]
    assert "sintese" in body
    assert body["auth_valid"] is True


def test_consulta_usa_dados_default_quando_paciente_e_medico_omitidos(client):
    resp = client.post("/api/consulta", json={"relato": "Relato sem paciente nem medico informados."})
    assert resp.status_code == 200


def test_auditoria_retorna_lista(client):
    resp = client.get("/api/auditoria")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["events"], list)


def test_documentos_retorna_lista(client):
    resp = client.get("/api/documentos")
    assert resp.status_code == 200
    assert isinstance(resp.json()["documents"], list)


def test_download_arquivo_inexistente_retorna_404(client):
    resp = client.get("/api/download", params={"path": "arquivo_que_nao_existe_123.pdf"})
    assert resp.status_code == 404


def test_download_exige_parametro_path(client):
    resp = client.get("/api/download")
    assert resp.status_code == 422
