# Plano de entrega — Tech Challenge Fase 3

Somente o que o enunciado exige. O percentual indica quanto do item já está pronto no `main` em 13/09/2026. Cada passo traz, marcado como (bloqueante), o motivo pelo qual bloqueia a entrega, seguido da citação do enunciado que sustenta isso.

**Progresso geral estimado: 96%**

## Situação de cada item

- [x] Fine-tuning com protocolos, perguntas de médicos e modelos de laudo/receita
- [x] Preprocessing, anonimização e curadoria dos dados
- [x] Pipeline LangChain integrando a LLM customizada
- [x] Consultas em base estruturada de prontuários
- [x] Contextualizar as respostas com dados do paciente
- [x] Nunca prescrever sem validação humana
- [x] Logging detalhado para rastreamento e auditoria
- [x] Explainability: indicar a fonte da informação
- [x] Projeto modularizado em Python
- [x] Instruções completas no README
- [x] Repositório: pipeline de fine-tuning
- [x] Repositório: integração com LangChain
- [x] Repositório: fluxos do LangGraph
- [x] Dataset anonimizado ou exemplo de dados sintéticos
- [x] Relatório: explicação do processo de fine-tuning
- [ ] Relatório: descrição do assistente criado — 70%
- [x] Relatório: diagrama do fluxo LangChain
- [x] Relatório: avaliação do modelo e análise dos resultados
- [ ] Vídeo de até 15 minutos — 0%

Faltam dois itens, e nenhum deles é do fine-tuning.

**Como ler as citações:** referem-se ao enunciado oficial, [8IADT - Fase 3 - Tech challenge.pdf](8IADT%20-%20Fase%203%20-%20Tech%20challenge.pdf), versionado na raiz do repositório. A linha é contada de cima para baixo, sem contar o cabeçalho "Tech Challenge Página X de 5". Na página 4, cada linha visual da tabela de datasets conta como uma linha.

## 1. Fine-tuning de LLM com dados médicos internos

* ~~Fine-tuning de LLM com protocolos, perguntas de médicos e modelos de laudo/receita~~ (100%)
   * O adapter atual foi treinado só com MedQuAD, que são perguntas gerais de saúde. Os três tipos de dado pedidos não estão no treino.
      > (pág 2, linhas 21-25) "Realizar o fine-tuning de um modelo LLM (como LLaMA, Falcon ou um outro) utilizando: Protocolos médicos do hospital; Exemplos de perguntas frequentes feitas por médicos; Modelos de laudos, receitas e procedimentos internos."
      >
      > (pág 2, linhas 9-10) "criar um assistente virtual médico treinado com os dados próprios do hospital"
   * ~~Criar dataset sintético com protocolos internos do hospital, perguntas frequentes de médicos e modelos de laudo, receita e procedimento.~~ Feito: 42 exemplos em `data/raw/dados_internos_hospital.jsonl`.
      > (bloqueante) O fine-tuning precisa usar esses três tipos de dado, e hoje eles não existem no projeto. Como não há dados reais de hospital, o enunciado aceita dados sintéticos.
      >
      > (pág 2, linhas 23-25) "Protocolos médicos do hospital; Exemplos de perguntas frequentes feitas por médicos; Modelos de laudos, receitas e procedimentos internos."
      >
      > (pág 3, linha 23) "Dataset anonimizado ou exemplo de dados sintéticos;"
   * ~~Passar o novo dataset pelo pipeline de preprocessing, anonimização e validação de `backend/src/data`.~~ Feito: 42 de 42 aprovados, nota 100.
      > (bloqueante) Todo dado usado no treino precisa passar por essa preparação.
      >
      > (pág 2, linhas 26-27) "Preparar os dados com técnicas de preprocessing, anonimização e curadoria."
   * ~~Treinar nova versão do adapter incluindo o dataset interno.~~ Feito em 2,4 min numa g6.xlarge, por `backend/src/data/05_treinar_adapter.py`. Loss de 1,39 para 0,15.
      > (bloqueante) Sem novo treino, o modelo continua sem os dados pedidos.
      >
      > (pág 2, linhas 21-22) "Realizar o fine-tuning de um modelo LLM (como LLaMA, Falcon ou um outro) utilizando:"
   * ~~Avaliar o novo adapter e atualizar a seção de avaliação do relatório.~~ Feito: perplexidade nos dados internos caiu de 5,43 para 1,78, e no MedQuAD de 1,83 para 1,61, sem esquecimento. Seção 5.6 do relatório técnico.
      > (bloqueante) O relatório precisa avaliar o modelo entregue, e o modelo entregue passa a ser o novo adapter.
      >
      > (pág 4, linha 3) "Avaliação do modelo e análise dos resultados."
   * ~~Apontar `LLM_MODEL` para o novo adapter.~~ Feito: o assistente usa `biomistral-medassist-lora`, treinado na máquina da AWS.
      > (bloqueante) Sem isso, o assistente continua usando o adapter antigo, que não foi treinado com os dados pedidos.
      >
      > (pág 3, linhas 2-3) "Utilizar o LangChain para: Construir um pipeline que integre a LLM customizada;"
* ~~Preprocessing, anonimização e curadoria dos dados~~ (100%)
   * Pronto. Scripts de anonimização, normalização, split e validação em `backend/src/data`, com relatórios gerados.
      > (pág 2, linhas 26-27) "Preparar os dados com técnicas de preprocessing, anonimização e curadoria."

## 2. Assistente médico com LangChain

* ~~Pipeline LangChain integrando a LLM customizada~~ (100%)
   * Feito. `BioMistralChatModel` (`backend/src/llm/langchain_client.py`) encapsula o `LLMClient` como chat model do `langchain-core` (`BaseChatModel`). A API (`backend/src/api/app.py`) monta o grafo com `criar_workflow(get_langchain_llm(), ...)` e chama `grafo.invoke(state)` — o LangGraph roda de ponta a ponta numa única chamada, em vez de a API chamar os nós um a um. `triar()`/`sintetizar()` usam a interface do langchain-core (`SystemMessage`/`HumanMessage`) quando recebem esse client.
      > (pág 3, linhas 2-3) "Utilizar o LangChain para: Construir um pipeline que integre a LLM customizada;"
      >
      > (pág 3, linhas 19 e 22) "Código-fonte com: [...] Fluxos do LangGraph."
      >
      > (pág 4, linha 14) "Execução de um fluxo automatizado;"
* ~~Consultas em base de dados estruturada, como prontuários e registros~~ (100%)
   * Feito. Base SQLite sintética de prontuários (`backend/src/data/prontuarios.py`, `ProntuarioStore`, 4 pacientes sintéticos com histórico/alergias/condições crônicas) consultada por uma tool do langchain-core (`backend/src/graph/tools.py`, `consultar_prontuario`).
      > (pág 3, linhas 2 e 4-5) "Utilizar o LangChain para: [...] Realizar consultas em base de dados estruturadas (como prontuários e registros);"
      >
      > (pág 3, linha 23) "Dataset anonimizado ou exemplo de dados sintéticos;"
* ~~Contextualizar as respostas com informações atualizadas do paciente~~ (100%)
   * Feito. Novo nó `node_contexto_paciente` (`backend/src/graph/nodes.py`) roda logo após a triagem, chama a tool acima e grava `historico_paciente` no estado; `node_sintese` passa esse histórico pra `sintetizar()`, que o injeta no prompt da LLM (`_formatar_historico`). A API recebe `paciente_id` no payload de `/api/consulta` e propaga pro estado inicial do grafo.
      > (pág 3, linhas 2 e 6-7) "Utilizar o LangChain para: [...] Contextualizar as respostas da LLM com informações atualizadas do paciente."
      >
      > (pág 4, linha 15) "Resposta a perguntas clínicas contextualizadas;"

## 3. Segurança e validação

* ~~Limites de atuação: nunca prescrever sem validação humana~~ (100%)
   * Feito. A consulta agora é dividida em duas etapas de verdade, usando `interrupt()`/checkpointer do LangGraph (não é mais um `medico_decisao` hardcoded): `POST /api/consulta` roda o grafo até o nó `hitl`, que pausa a execução — devolve `status: "aguardando_validacao"` e **nenhum documento**. Só `POST /api/consulta/{session_id}/decisao` (aprovar/editar/rejeitar) retoma o grafo; o documento só é gerado se a decisão for "aprovado" ou "editado" (`node_gerar_docs` em `backend/src/graph/nodes.py`). O estado pausado sobrevive entre as duas chamadas HTTP via checkpointer SQLite (`backend/src/graph/workflow.py`, `data/processed/checkpoints.db`). UI de aprovar/editar/rejeitar adicionada em `frontend/src/components/ConsultaPanel.jsx`.
      > (pág 3, linhas 9-10) "Definir limites de atuação do assistente para evitar sugestões impróprias (ex.: nunca prescrever diretamente, sem validação humana);"
      >
      > (pág 4, linha 16) "Logs e validação das respostas."
* ~~Logging detalhado para rastreamento e auditoria~~ (100%)
   * Feito. `POST /api/consulta` e `POST /api/consulta/{session_id}/decisao` rodam o grafo via `.stream(..., stream_mode="updates")` e gravam um evento de auditoria por etapa concluída (`_log_etapa` em `backend/src/api/app.py`, usando os dataclasses tipados já existentes em `backend/src/logging/schemas.py`): `triagem`, `contexto_paciente`, `retrieval` (com as fontes), `sintese`, `validacao`, `hitl_decisao` (a decisão do médico) e `documento_gerado`.
      > (pág 3, linha 11) "Implementar logging detalhado para rastreamento e auditoria;"
      >
      > (pág 4, linha 16) "Logs e validação das respostas."
* ~~Explainability: indicar a fonte da informação~~ (100%)
   * Pronto. A resposta da API traz a fonte de cada trecho recuperado pelo RAG, e o prompt da síntese exige citação da fonte.
      > (pág 3, linhas 12-13) "Garantir explainability das respostas da LLM (exemplo: indicar a fonte da informação utilizada na resposta)."

## 4. Organização do código

* ~~Projeto modularizado em Python~~ (100%)
   * Pronto. O código está separado em módulos dentro de `backend/src`.
      > (pág 3, linha 15) "Projeto modularizado em Python;"
* ~~Instruções completas no README~~ (100%)
   * Feito. `README.md` (raiz) ganhou a seção "Rodando com o modelo real" (`LLM_MOCK`, `LLM_MODEL`) e a explicação do fluxo HITL em 2 etapas. `backend/README.md` ganhou a tabela completa de variáveis de ambiente (`LLM_MOCK`, `LLM_MODEL`, `LLM_BASE_MODEL`) e a seção "Gerar os dados que o backend consome" (índice RAG via `build_index_chatbulario.py`, base de prontuários auto-inicializada). Documentado honestamente o caveat de `build_index_local.py` (caminho hardcoded de outra máquina, collection `anvisa` obsoleta) em vez de mascarar.
      > (pág 3, linha 16) "Instruções completas no README."

## 5. Entregáveis

* ~~Repositório: pipeline de fine-tuning~~ (100%)
   * Pronto. `notebooks/02_finetuning.ipynb` com QLoRA sobre o BioMistral-7B.
      > (pág 3, linhas 18-20) "Repositório Git: Código-fonte com: Pipeline de fine-tuning;"
* ~~Repositório: integração com LangChain~~ (100%)
   * Coberto pelos passos da seção 2 — feito.
      > (pág 3, linhas 19 e 21) "Código-fonte com: [...] Integração com LangChain;"
* ~~Repositório: fluxos do LangGraph~~ (100%)
   * Feito. A API executa o grafo compilado (`criar_workflow(...).stream(state, ...)`) de ponta a ponta, com pausa real no nó `hitl` via `interrupt()`.
      > (pág 3, linhas 19 e 22) "Código-fonte com: [...] Fluxos do LangGraph."
* ~~Dataset anonimizado ou exemplo de dados sintéticos~~ (100%)
   * Pronto. As notas clínicas sintéticas estão versionadas em `data/raw/synthetic_clinical_notes`. O enunciado aceita anonimizado ou sintético.
      > (pág 3, linha 23) "Dataset anonimizado ou exemplo de dados sintéticos;"
* ~~Relatório: explicação do processo de fine-tuning~~ (100%)
   * Pronto. Seções 2.2, 2.3 e 4 do relatório técnico.
      > (pág 3, linhas 24-25) "Relatório técnico detalhado com: Explicação do processo de fine-tuning;"
* Relatório: descrição do assistente criado (70%)
   * O texto ainda descreve o Gradio em outras seções. A parte específica sobre a pausa com `interrupt()` deixou de ser uma imprecisão — o `interrupt()` agora existe de verdade no código (seção 3 deste plano), e a seção 2.6-2.7 do relatório foi atualizada junto com o diagrama abaixo para descrever o fluxo real de 7 nós e a API em 2 etapas.
      > (pág 4, linha 1) "Descrição do assistente médico criado;"
   * Reescrever o restante do relatório (fora da seção 2.6-2.7) para não citar mais o Gradio.
      > (bloqueante) A descrição em outras seções ainda não corresponde ao assistente entregue.
      >
      > (pág 4, linha 1) "Descrição do assistente médico criado;"
* ~~Relatório: diagrama do fluxo LangChain~~ (100%)
   * Feito. Diagrama Mermaid em `docs/RELATORIO_TECNICO_PARA_EQUIPE.md` (seção 2.6), mostrando os 7 nós reais do grafo e a divisão em 2 fases (`POST /api/consulta` até o `interrupt()` no `hitl`, `POST /api/consulta/{session_id}/decisao` retomando via `Command(resume=...)`).
      > (pág 4, linha 2) "Diagrama do fluxo LangChain."
* ~~Relatório: avaliação do modelo e análise dos resultados~~ (100%)
   * Pronto. Perplexidade base contra fine-tunado, testes de generalização e análise de overfitting nas seções 4 e 5.
      > (pág 4, linha 3) "Avaliação do modelo e análise dos resultados."
* Vídeo de até 15 minutos (0%)
   * Não gravado. Hoje o modelo real não roda em lugar nenhum: o notebook do Colab chama o `gradio_app.py`, que foi apagado.
      > (pág 4, linhas 11-16) "Vídeo com até 15 minutos demonstrando: Assistente médico: Treinamento e funcionamento da LLM personalizada; Execução de um fluxo automatizado; Resposta a perguntas clínicas contextualizadas; Logs e validação das respostas."
   * Consertar `notebooks/rodarcolab.ipynb` para rodar o assistente com a LLM personalizada: usar `backend/src` e `backend/requirements.txt` e remover a chamada ao `gradio_app.py`.
      > (bloqueante) Hoje a LLM personalizada não roda em lugar nenhum, e o vídeo precisa mostrar o funcionamento dela.
      >
      > (pág 4, linha 13) "Treinamento e funcionamento da LLM personalizada;"
   * Gravar e entregar o vídeo cobrindo os quatro pontos da citação acima.
      > (bloqueante) É o próprio entregável.
      >
      > (pág 4, linha 11) "Vídeo com até 15 minutos demonstrando:"

## Fora deste plano

* Alertas para a equipe médica e verificação de exames pendentes
   * Aparecem no enunciado apenas como exemplo de fluxo, não na lista de requisitos obrigatórios.
      > (pág 2, linhas 14-16) "por exemplo, ao receber informações sobre um paciente, o sistema possa acionar diferentes etapas, como verificar exames pendentes, sugerir tratamentos e emitir alertas para a equipe médica"
