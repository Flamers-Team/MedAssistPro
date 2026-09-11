# Plano de entrega — Tech Challenge Fase 3

Somente o que o enunciado exige. O percentual indica quanto do item já está pronto no `main` em 11/09/2026 (commit `e36cb1a`). Cada passo traz, marcado como (bloqueante), o motivo pelo qual bloqueia a entrega, seguido da citação do enunciado que sustenta isso.

**Progresso geral estimado: 58%**

**Como ler as citações:** referem-se ao enunciado oficial, [8IADT - Fase 3 - Tech challenge.pdf](8IADT%20-%20Fase%203%20-%20Tech%20challenge.pdf), versionado na raiz do repositório. A linha é contada de cima para baixo, sem contar o cabeçalho "Tech Challenge Página X de 5". Na página 4, cada linha visual da tabela de datasets conta como uma linha.

## 1. Fine-tuning de LLM com dados médicos internos

* Fine-tuning de LLM com protocolos, perguntas de médicos e modelos de laudo/receita (60%)
   * O adapter atual foi treinado só com MedQuAD, que são perguntas gerais de saúde. Os três tipos de dado pedidos não estão no treino.
      > (pág 2, linhas 21-25) "Realizar o fine-tuning de um modelo LLM (como LLaMA, Falcon ou um outro) utilizando: Protocolos médicos do hospital; Exemplos de perguntas frequentes feitas por médicos; Modelos de laudos, receitas e procedimentos internos."
      >
      > (pág 2, linhas 9-10) "criar um assistente virtual médico treinado com os dados próprios do hospital"
   * Criar dataset sintético com protocolos internos do hospital, perguntas frequentes de médicos e modelos de laudo, receita e procedimento.
      > (bloqueante) O fine-tuning precisa usar esses três tipos de dado, e hoje eles não existem no projeto. Como não há dados reais de hospital, o enunciado aceita dados sintéticos.
      >
      > (pág 2, linhas 23-25) "Protocolos médicos do hospital; Exemplos de perguntas frequentes feitas por médicos; Modelos de laudos, receitas e procedimentos internos."
      >
      > (pág 3, linha 23) "Dataset anonimizado ou exemplo de dados sintéticos;"
   * Passar o novo dataset pelo pipeline de preprocessing, anonimização e validação de `backend/src/data`.
      > (bloqueante) Todo dado usado no treino precisa passar por essa preparação.
      >
      > (pág 2, linhas 26-27) "Preparar os dados com técnicas de preprocessing, anonimização e curadoria."
   * Treinar nova versão do adapter incluindo o dataset interno, usando `notebooks/02_finetuning.ipynb`.
      > (bloqueante) Sem novo treino, o modelo continua sem os dados pedidos.
      >
      > (pág 2, linhas 21-22) "Realizar o fine-tuning de um modelo LLM (como LLaMA, Falcon ou um outro) utilizando:"
   * Avaliar o novo adapter e atualizar a seção de avaliação do relatório.
      > (bloqueante) O relatório precisa avaliar o modelo entregue, e o modelo entregue passa a ser o novo adapter.
      >
      > (pág 4, linha 3) "Avaliação do modelo e análise dos resultados."
   * Apontar `LLM_MODEL` para o novo adapter.
      > (bloqueante) Sem isso, o assistente continua usando o adapter antigo, que não foi treinado com os dados pedidos.
      >
      > (pág 3, linhas 2-3) "Utilizar o LangChain para: Construir um pipeline que integre a LLM customizada;"
* Preprocessing, anonimização e curadoria dos dados (100%)
   * Pronto. Scripts de anonimização, normalização, split e validação em `backend/src/data`, com relatórios gerados.
      > (pág 2, linhas 26-27) "Preparar os dados com técnicas de preprocessing, anonimização e curadoria."

## 2. Assistente médico com LangChain

* Pipeline LangChain integrando a LLM customizada (40%)
   * A LLM é chamada por um cliente próprio, fora do LangChain. O grafo LangGraph existe, mas a API chama os nós um a um em vez de executá-lo.
      > (pág 3, linhas 2-3) "Utilizar o LangChain para: Construir um pipeline que integre a LLM customizada;"
      >
      > (pág 2, linhas 13 e 17) "a ideia é organizar fluxos de decisão automatizados e seguros [...] tudo isso coordenado com LangChain."
   * Encapsular o `LLMClient` como um LLM do `langchain-core`.
      > (bloqueante) Hoje a LLM customizada é chamada fora do LangChain, então não existe pipeline LangChain que a integre.
      >
      > (pág 3, linhas 2-3) "Utilizar o LangChain para: Construir um pipeline que integre a LLM customizada;"
   * Fazer a API executar o grafo compilado por `criar_workflow` em vez de chamar os nós um a um.
      > (bloqueante) Sem isso, o fluxo do LangGraph nunca roda e não há fluxo automatizado para demonstrar.
      >
      > (pág 3, linhas 19 e 22) "Código-fonte com: [...] Fluxos do LangGraph."
      >
      > (pág 4, linha 14) "Execução de um fluxo automatizado;"
* Consultas em base de dados estruturada, como prontuários e registros (0%)
   * Não existe base de pacientes. O RAG consulta bulas, CID-10 e notas genéricas por busca semântica, que não é consulta estruturada nem registro do paciente em atendimento.
      > (pág 3, linhas 2 e 4-5) "Utilizar o LangChain para: [...] Realizar consultas em base de dados estruturadas (como prontuários e registros);"
   * Criar uma base de dados estruturada de prontuários, com dados sintéticos ou anonimizados.
      > (bloqueante) Não existe base estruturada para ser consultada.
      >
      > (pág 3, linhas 4-5) "Realizar consultas em base de dados estruturadas (como prontuários e registros);"
      >
      > (pág 3, linha 23) "Dataset anonimizado ou exemplo de dados sintéticos;"
   * Criar uma tool do LangChain que consulta essa base por paciente.
      > (bloqueante) O enunciado pede que as consultas sejam feitas com o LangChain.
      >
      > (pág 3, linhas 2 e 4-5) "Utilizar o LangChain para: [...] Realizar consultas em base de dados estruturadas (como prontuários e registros);"
* Contextualizar as respostas com informações atualizadas do paciente (10%)
   * Hoje os dados do paciente só vão para o PDF e nunca chegam ao modelo. A consulta também não identifica o paciente, então não há registro a buscar.
      > (pág 3, linhas 2 e 6-7) "Utilizar o LangChain para: [...] Contextualizar as respostas da LLM com informações atualizadas do paciente."
   * Criar nó no grafo que consulta o prontuário do paciente pela tool e injeta o histórico no prompt da LLM.
      > (bloqueante) Sem ele, as informações do paciente não chegam à LLM.
      >
      > (pág 3, linhas 6-7) "Contextualizar as respostas da LLM com informações atualizadas do paciente."
   * Fazer a API receber o identificador do paciente na consulta.
      > (bloqueante) Sem identificar o paciente, não há prontuário a consultar e a resposta não fica contextualizada.
      >
      > (pág 3, linhas 6-7) "Contextualizar as respostas da LLM com informações atualizadas do paciente."
      >
      > (pág 4, linha 15) "Resposta a perguntas clínicas contextualizadas;"

## 3. Segurança e validação

* Limites de atuação: nunca prescrever sem validação humana (50%)
   * Prompts e marcação de medicações já existem. A validação humana foi perdida na migração para a API, que aprova sozinha e já gera o PDF.
      > (pág 3, linhas 9-10) "Definir limites de atuação do assistente para evitar sugestões impróprias (ex.: nunca prescrever diretamente, sem validação humana);"
   * Dividir a consulta em duas etapas. A primeira devolve só a sugestão, sem gerar documento.
      > (bloqueante) Hoje o documento é gerado sem validação humana.
      >
      > (pág 3, linhas 9-10) "nunca prescrever diretamente, sem validação humana"
   * Criar rota de decisão do médico: aprovar, editar ou rejeitar. O documento só é gerado após aprovar ou editar.
      > (bloqueante) Sem ela, o médico não tem como validar a resposta antes da emissão do documento.
      >
      > (pág 3, linhas 9-10) "nunca prescrever diretamente, sem validação humana"
      >
      > (pág 4, linha 16) "Logs e validação das respostas."
* Logging detalhado para rastreamento e auditoria (50%)
   * Hoje a API grava um único evento por consulta, sem detalhe por etapa.
      > (pág 3, linha 11) "Implementar logging detalhado para rastreamento e auditoria;"
   * Registrar um evento por etapa: triagem, retrieval com as fontes, consulta ao prontuário, síntese, validação, decisão do médico e documento gerado.
      > (bloqueante) Com um único evento por consulta, não dá para rastrear o que cada etapa fez.
      >
      > (pág 3, linha 11) "Implementar logging detalhado para rastreamento e auditoria;"
      >
      > (pág 4, linha 16) "Logs e validação das respostas."
* Explainability: indicar a fonte da informação (100%)
   * Pronto. A resposta da API traz a fonte de cada trecho recuperado pelo RAG, e o prompt da síntese exige citação da fonte.
      > (pág 3, linhas 12-13) "Garantir explainability das respostas da LLM (exemplo: indicar a fonte da informação utilizada na resposta)."

## 4. Organização do código

* Projeto modularizado em Python (100%)
   * Pronto. O código está separado em módulos dentro de `backend/src`.
      > (pág 3, linha 15) "Projeto modularizado em Python;"
* Instruções completas no README (70%)
   * O README explica backend e frontend, mas não explica como rodar com o modelo real nem como gerar os dados.
      > (pág 3, linha 16) "Instruções completas no README."
   * Documentar como rodar com o modelo real, as variáveis de ambiente (`LLM_MOCK`, `LLM_MODEL`) e a geração da base de prontuários e do índice RAG.
      > (bloqueante) Sem isso, o README não permite rodar o projeto com a LLM personalizada nem gerar os dados de que ele depende.
      >
      > (pág 3, linha 16) "Instruções completas no README."

## 5. Entregáveis

* Repositório: pipeline de fine-tuning (100%)
   * Pronto. `notebooks/02_finetuning.ipynb` com QLoRA sobre o BioMistral-7B.
      > (pág 3, linhas 18-20) "Repositório Git: Código-fonte com: Pipeline de fine-tuning;"
* Repositório: integração com LangChain (40%)
   * Coberto pelos passos da seção 2.
      > (pág 3, linhas 19 e 21) "Código-fonte com: [...] Integração com LangChain;"
* Repositório: fluxos do LangGraph (30%)
   * O grafo existe, mas nunca é executado. Coberto pelo passo da seção 2 que faz a API executar o grafo.
      > (pág 3, linhas 19 e 22) "Código-fonte com: [...] Fluxos do LangGraph."
* Dataset anonimizado ou exemplo de dados sintéticos (100%)
   * Pronto. As notas clínicas sintéticas estão versionadas em `data/raw/synthetic_clinical_notes`. O enunciado aceita anonimizado ou sintético.
      > (pág 3, linha 23) "Dataset anonimizado ou exemplo de dados sintéticos;"
* Relatório: explicação do processo de fine-tuning (100%)
   * Pronto. Seções 2.2, 2.3 e 4 do relatório técnico.
      > (pág 3, linhas 24-25) "Relatório técnico detalhado com: Explicação do processo de fine-tuning;"
* Relatório: descrição do assistente criado (60%)
   * O texto descreve o Gradio e uma pausa com `interrupt()` que não existe no código.
      > (pág 4, linha 1) "Descrição do assistente médico criado;"
   * Reescrever para descrever o assistente como ele está no código entregue.
      > (bloqueante) A descrição atual não corresponde ao assistente entregue.
      >
      > (pág 4, linha 1) "Descrição do assistente médico criado;"
* Relatório: diagrama do fluxo LangChain (0%)
   * Não há diagrama em nenhum documento. Existe só uma linha de texto com setas.
      > (pág 4, linha 2) "Diagrama do fluxo LangChain."
   * Criar o diagrama do fluxo do grafo final e incluir no relatório técnico.
      > (bloqueante) O diagrama não existe.
      >
      > (pág 4, linha 2) "Diagrama do fluxo LangChain."
* Relatório: avaliação do modelo e análise dos resultados (100%)
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
