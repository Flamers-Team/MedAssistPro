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


def _iniciar_consulta(client, **overrides):
    payload = {
        "relato": "Paciente relata febre e tosse ha 3 dias, sem dispneia.",
        "paciente": {"nome": "Teste", "idade": "30", "sexo": "M"},
        "medico": {"nome": "Dr Teste", "crm": "11111"},
    }
    payload.update(overrides)
    return client.post("/api/consulta", json=payload)


def test_consulta_fica_aguardando_validacao_e_nao_gera_documento(client):
    resp = _iniciar_consulta(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "aguardando_validacao"
    assert "session_id" in body
    assert "triagem" in body and "categoria" in body["triagem"]
    assert "sintese" in body
    assert body["documento"] is None
    assert body["hash_documento"] is None
    assert body["auth_valid"] is True


def test_consulta_com_paciente_id_roda_o_grafo_completo(client):
    resp = _iniciar_consulta(
        client,
        relato="Retorno para reavaliar dor toracica ao esforco.",
        paciente_id="PAC-0002",
        paciente={"nome": "Carlos Eduardo Lima", "idade": "61", "sexo": "M"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "aguardando_validacao"
    assert "triagem" in body
    assert "sintese" in body


def test_consulta_usa_dados_default_quando_paciente_e_medico_omitidos(client):
    resp = client.post("/api/consulta", json={"relato": "Relato sem paciente nem medico informados."})
    assert resp.status_code == 200
    assert resp.json()["status"] == "aguardando_validacao"


def test_decisao_aprovado_gera_documento(client):
    session_id = _iniciar_consulta(client).json()["session_id"]

    resp = client.post(f"/api/consulta/{session_id}/decisao", json={"decisao": "aprovado"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in ("ok", "partial")
    assert body["documento"] is not None
    assert body["hash_documento"] is not None


def test_decisao_rejeitado_nao_gera_documento(client):
    session_id = _iniciar_consulta(client).json()["session_id"]

    resp = client.post(f"/api/consulta/{session_id}/decisao", json={"decisao": "rejeitado"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "rejeitado"
    assert body["documento"] is None
    assert body["hash_documento"] is None


def test_decisao_editado_usa_texto_editado(client):
    session_id = _iniciar_consulta(client).json()["session_id"]

    resp = client.post(
        f"/api/consulta/{session_id}/decisao",
        json={"decisao": "editado", "texto_editado": "Texto revisado pelo medico."},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in ("ok", "partial")
    assert body["documento"] is not None


def test_decisao_com_sessao_inexistente_retorna_404(client):
    resp = client.post("/api/consulta/sessao-que-nao-existe/decisao", json={"decisao": "aprovado"})
    assert resp.status_code == 404


def test_decisao_duplicada_retorna_409(client):
    session_id = _iniciar_consulta(client).json()["session_id"]
    client.post(f"/api/consulta/{session_id}/decisao", json={"decisao": "aprovado"})

    resp = client.post(f"/api/consulta/{session_id}/decisao", json={"decisao": "aprovado"})
    assert resp.status_code == 409


def test_decisao_rejeita_valor_invalido(client):
    session_id = _iniciar_consulta(client).json()["session_id"]

    resp = client.post(f"/api/consulta/{session_id}/decisao", json={"decisao": "talvez"})
    assert resp.status_code == 422


def test_fluxo_completo_gera_um_evento_de_auditoria_por_etapa(client):
    session_id = _iniciar_consulta(client).json()["session_id"]
    client.post(f"/api/consulta/{session_id}/decisao", json={"decisao": "aprovado"})

    eventos = client.get("/api/auditoria").json()["events"]
    tipos = {e["event_type"] for e in eventos if e["session_id"] == session_id}

    esperado = {"triagem", "contexto_paciente", "retrieval", "sintese", "validacao", "hitl_decisao", "documento_gerado"}
    assert esperado.issubset(tipos)


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
