"""Modelos de laudos, receitas e procedimentos internos do hospital.

Conteúdo sintético, criado para o Tech Challenge. Não é modelo institucional
real e não passou por validação clínica. Cada item vira um exemplo de treino:
o pedido do médico na entrada, o documento preenchido na saída.
"""

MODELOS = [
    {
        "pedido": "Gere o modelo de receita simples para paracetamol em adulto com dor leve.",
        "documento": """RECEITUÁRIO SIMPLES

Paciente: [NOME DO PACIENTE]
Data: [DATA]

1. Paracetamol 750 mg ................................... 1 caixa
   Tomar 1 comprimido por via oral a cada 8 horas, se dor ou febre.
   Dose máxima de 3 comprimidos em 24 horas. Uso por até 5 dias.

Orientações: não associar a outros medicamentos que contenham paracetamol.
Retornar se a dor persistir após 5 dias.

_______________________________
[NOME DO MÉDICO] — CRM [NÚMERO]

⚕️ Documento gerado com apoio de IA. Exige validação e assinatura do médico.""",
    },
    {
        "pedido": "Gere o modelo de receita de controle especial para um ansiolítico.",
        "documento": """RECEITUÁRIO DE CONTROLE ESPECIAL — 2 VIAS

Identificação do emitente: [NOME DO MÉDICO] — CRM [NÚMERO] — [ENDEREÇO] — [TELEFONE]

Paciente: [NOME DO PACIENTE]
Endereço do paciente: [ENDEREÇO]
Data: [DATA]

1. [MEDICAMENTO CONTROLADO] [CONCENTRAÇÃO] ............. [QUANTIDADE POR EXTENSO]
   Tomar [DOSE] por via oral [FREQUÊNCIA], por [DURAÇÃO].

Observação: prescrição válida por 30 dias em todo o território nacional.
1ª via retida no estabelecimento farmacêutico, 2ª via com o paciente.

_______________________________
[NOME DO MÉDICO] — CRM [NÚMERO]

⚕️ Documento gerado com apoio de IA. Exige validação e assinatura do médico.""",
    },
    {
        "pedido": "Gere o modelo de atestado médico de afastamento por 2 dias.",
        "documento": """ATESTADO MÉDICO

Atesto, para os devidos fins, que o(a) paciente [NOME DO PACIENTE],
portador(a) do documento [DOCUMENTO], esteve sob meus cuidados profissionais
nesta data e necessita de afastamento de suas atividades por 2 (dois) dias,
a contar de [DATA INICIAL].

CID: [CÓDIGO] (informado mediante autorização expressa do paciente)

Local e data: [CIDADE], [DATA]

_______________________________
[NOME DO MÉDICO] — CRM [NÚMERO]

⚕️ Documento gerado com apoio de IA. Exige validação e assinatura do médico.""",
    },
    {
        "pedido": "Gere o modelo de laudo de radiografia de tórax normal.",
        "documento": """LAUDO DE RADIOGRAFIA DE TÓRAX

Paciente: [NOME DO PACIENTE]        Idade: [IDADE]
Exame: Radiografia de tórax em PA e perfil
Data do exame: [DATA]
Indicação clínica: [INDICAÇÃO]

TÉCNICA: incidências em PA e perfil, em inspiração adequada.

ACHADOS:
- Campos pulmonares sem opacidades ou consolidações.
- Seios costofrênicos livres.
- Área cardíaca dentro dos limites da normalidade.
- Mediastino centrado, sem alargamento.
- Arcabouço ósseo sem alterações evidentes.

CONCLUSÃO: exame dentro dos limites da normalidade.

_______________________________
[NOME DO MÉDICO] — CRM [NÚMERO]

⚕️ Documento gerado com apoio de IA. Exige validação e assinatura do médico.""",
    },
    {
        "pedido": "Gere o modelo de relatório de alta hospitalar após internação clínica.",
        "documento": """RELATÓRIO DE ALTA HOSPITALAR

Paciente: [NOME DO PACIENTE]        Registro: [NÚMERO]
Internação: [DATA DE ENTRADA] a [DATA DE ALTA]
Motivo da internação: [MOTIVO]

RESUMO DA INTERNAÇÃO:
[EVOLUÇÃO CLÍNICA, EXAMES RELEVANTES E TRATAMENTO REALIZADO]

DIAGNÓSTICO DE ALTA: [DIAGNÓSTICO] — CID [CÓDIGO]

CONDIÇÕES DE ALTA: paciente estável, orientado, deambulando, aceitando dieta.

PRESCRIÇÃO DE ALTA:
1. [MEDICAMENTO] — [DOSE] — [FREQUÊNCIA] — [DURAÇÃO]

ORIENTAÇÕES: retorno ambulatorial em [PRAZO]. Procurar pronto atendimento
em caso de [SINAIS DE ALERTA].

_______________________________
[NOME DO MÉDICO] — CRM [NÚMERO]

⚕️ Documento gerado com apoio de IA. Exige validação e assinatura do médico.""",
    },
    {
        "pedido": "Gere o modelo de encaminhamento para especialista.",
        "documento": """ENCAMINHAMENTO AMBULATORIAL

Para: [ESPECIALIDADE]
Paciente: [NOME DO PACIENTE]        Idade: [IDADE]
Data: [DATA]

MOTIVO DO ENCAMINHAMENTO: [RESUMO DA QUEIXA E DA HIPÓTESE]

HISTÓRIA CLÍNICA RESUMIDA: [ANTECEDENTES, TEMPO DE EVOLUÇÃO E TRATAMENTOS JÁ TENTADOS]

EXAMES REALIZADOS: [LISTA COM DATAS E RESULTADOS PRINCIPAIS]

MEDICAÇÕES EM USO: [LISTA]

Agradeço a avaliação e permaneço à disposição.

_______________________________
[NOME DO MÉDICO] — CRM [NÚMERO]

⚕️ Documento gerado com apoio de IA. Exige validação e assinatura do médico.""",
    },
    {
        "pedido": "Gere o modelo de prontuário de atendimento em pronto-socorro.",
        "documento": """PRONTUÁRIO DE ATENDIMENTO

Paciente: [NOME DO PACIENTE]        Idade: [IDADE]        Sexo: [SEXO]
Data e hora: [DATA E HORA]        Classificação de risco: [COR]

QUEIXA PRINCIPAL: [QUEIXA]

HISTÓRIA DA DOENÇA ATUAL: [EVOLUÇÃO, TEMPO, FATORES DE MELHORA E PIORA]

ANTECEDENTES: [COMORBIDADES, MEDICAÇÕES, ALERGIAS]

EXAME FÍSICO: [SINAIS VITAIS E ACHADOS POR SISTEMA]

HIPÓTESES DIAGNÓSTICAS: [LISTA COM CID]

CONDUTA: [EXAMES, MEDICAÇÕES E DESTINO DO PACIENTE]

_______________________________
[NOME DO MÉDICO] — CRM [NÚMERO]

⚕️ Documento gerado com apoio de IA. Exige validação e assinatura do médico.""",
    },
    {
        "pedido": "Gere o modelo de solicitação de exames complementares.",
        "documento": """SOLICITAÇÃO DE EXAMES

Paciente: [NOME DO PACIENTE]        Data: [DATA]
Hipótese diagnóstica: [HIPÓTESE] — CID [CÓDIGO]

SOLICITO:
1. [EXAME] — justificativa: [MOTIVO CLÍNICO]
2. [EXAME] — justificativa: [MOTIVO CLÍNICO]

Preparo necessário: [JEJUM OU OUTRAS ORIENTAÇÕES]
Prioridade: [ROTINA / URGENTE]

_______________________________
[NOME DO MÉDICO] — CRM [NÚMERO]

⚕️ Documento gerado com apoio de IA. Exige validação e assinatura do médico.""",
    },
    {
        "pedido": "Gere o modelo de laudo de eletrocardiograma com ritmo sinusal normal.",
        "documento": """LAUDO DE ELETROCARDIOGRAMA

Paciente: [NOME DO PACIENTE]        Idade: [IDADE]
Data do exame: [DATA]        Indicação: [INDICAÇÃO]

ACHADOS:
- Ritmo: sinusal.
- Frequência cardíaca: [VALOR] batimentos por minuto.
- Eixo elétrico: dentro da faixa normal.
- Intervalo PR e duração do QRS dentro dos limites da normalidade.
- Repolarização ventricular sem alterações agudas.

CONCLUSÃO: eletrocardiograma dentro dos limites da normalidade.
O laudo não exclui doença coronariana. Correlacionar com a clínica.

_______________________________
[NOME DO MÉDICO] — CRM [NÚMERO]

⚕️ Documento gerado com apoio de IA. Exige validação e assinatura do médico.""",
    },
    {
        "pedido": "Gere o modelo de termo de consentimento para procedimento.",
        "documento": """TERMO DE CONSENTIMENTO LIVRE E ESCLARECIDO

Paciente: [NOME DO PACIENTE]        Documento: [DOCUMENTO]
Procedimento proposto: [PROCEDIMENTO]

Declaro que fui informado(a), em linguagem acessível, sobre:
1. A natureza e o objetivo do procedimento.
2. Os benefícios esperados.
3. Os riscos e as complicações possíveis: [RISCOS].
4. As alternativas de tratamento disponíveis.
5. O direito de revogar este consentimento a qualquer momento.

Tive oportunidade de fazer perguntas e todas foram respondidas.

[CIDADE], [DATA]

_______________________________        _______________________________
Paciente ou responsável                [NOME DO MÉDICO] — CRM [NÚMERO]

⚕️ Documento gerado com apoio de IA. Exige validação e assinatura do médico.""",
    },
    {
        "pedido": "Gere o modelo de declaração de comparecimento para acompanhante.",
        "documento": """DECLARAÇÃO DE COMPARECIMENTO

Declaro, para os devidos fins, que [NOME DO ACOMPANHANTE], documento
[DOCUMENTO], compareceu a esta unidade na data de [DATA], no período das
[HORA INICIAL] às [HORA FINAL], acompanhando o(a) paciente [NOME DO PACIENTE].

Esta declaração não constitui atestado médico e não informa diagnóstico.

[CIDADE], [DATA]

_______________________________
[NOME DO MÉDICO] — CRM [NÚMERO]

⚕️ Documento gerado com apoio de IA. Exige validação e assinatura do médico.""",
    },
    {
        "pedido": "Gere o modelo de evolução diária de paciente internado.",
        "documento": """EVOLUÇÃO DIÁRIA

Paciente: [NOME DO PACIENTE]        Leito: [LEITO]        Dia de internação: [NÚMERO]
Data e hora: [DATA E HORA]

SUBJETIVO: [QUEIXAS E RELATO DO PACIENTE NAS ÚLTIMAS 24 HORAS]

OBJETIVO: sinais vitais [VALORES]; exame físico [ACHADOS];
exames do dia [RESULTADOS].

AVALIAÇÃO: [INTERPRETAÇÃO DA EVOLUÇÃO E DIAGNÓSTICOS ATIVOS]

PLANO: [AJUSTES DE MEDICAÇÃO, EXAMES SOLICITADOS, METAS E PREVISÃO DE ALTA]

_______________________________
[NOME DO MÉDICO] — CRM [NÚMERO]

⚕️ Documento gerado com apoio de IA. Exige validação e assinatura do médico.""",
    },
]
