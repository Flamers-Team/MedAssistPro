"""Exemplos internos reservados para AVALIAÇÃO, fora do treino.

Mesmos três tipos do dataset de treino, escritos separadamente para medir se o
modelo aprendeu o formato ou apenas decorou os exemplos vistos.
"""

PROTOCOLOS_VAL = [
    {
        "relato": "Mulher de 67 anos com falta de ar súbita, dor no peito ao respirar e taquicardia, 10 dias após cirurgia de quadril.",
        "triagem": {
            "categoria": "EMERGENCIA",
            "justificativa": "Suspeita de embolia pulmonar no pós-operatório: avaliação imediata e exame de imagem.",
            "red_flags": ["dispneia súbita", "dor pleurítica", "pós-operatório recente"],
            "confianca": "alta",
        },
    },
    {
        "relato": "Homem de 41 anos com dor abdominal em faixa, irradiando para o dorso, vômitos e história de etilismo.",
        "triagem": {
            "categoria": "URGENTE",
            "justificativa": "Quadro compatível com pancreatite aguda: exames laboratoriais, hidratação e analgesia.",
            "red_flags": ["dor em faixa", "vômitos persistentes"],
            "confianca": "media",
        },
    },
    {
        "relato": "Mulher de 31 anos com lesão eczematosa em antebraço há 3 semanas, sem febre, sem secreção.",
        "triagem": {
            "categoria": "ROTINA",
            "justificativa": "Lesão dermatológica crônica sem sinais infecciosos: avaliação ambulatorial.",
            "red_flags": [],
            "confianca": "alta",
        },
    },
]

DUVIDAS_VAL = [
    {
        "relato": "Paciente de 59 anos com fibrilação atrial recém-diagnosticada. Quais exames antes de anticoagular?",
        "historico": {"condicoes_cronicas": ["Hipertensão arterial"], "alergias": [], "historico": []},
        "rag": ["[Fonte: SOP-CARDIO-05] Antes da anticoagulação, avaliar função renal, hepática e hemograma, além do risco de sangramento."],
        "sintese": {
            "hipoteses": [
                {"cid10": "I48.9", "nome": "Fibrilação atrial não especificada", "probabilidade": "alta", "justificativa": "Diagnóstico recente confirmado.", "fonte": "SOP-CARDIO-05"},
            ],
            "exames_sugeridos": [
                {"nome": "Hemograma, função renal e hepática", "justificativa": "Definir escolha e dose do anticoagulante.", "fonte": "SOP-CARDIO-05"},
                {"nome": "Ecocardiograma", "justificativa": "Avaliar estrutura cardíaca e causas.", "fonte": "SOP-CARDIO-05"},
            ],
            "medicacoes_sugeridas": [
                {"nome": "Anticoagulante oral conforme escore de risco", "dose": "conforme função renal", "frequencia": "diária", "NOTA": "VALIDAÇÃO OBRIGATÓRIA"},
            ],
            "observacoes": "Calcular risco tromboembólico e hemorrágico antes de iniciar.",
        },
    },
    {
        "relato": "Paciente de 47 anos com anemia ferropriva sem causa aparente. O que investigar?",
        "historico": {"condicoes_cronicas": [], "alergias": [], "historico": []},
        "rag": ["[Fonte: SOP-CLIN-11] Anemia ferropriva em adulto exige investigação de perda digestiva antes de repor ferro isoladamente."],
        "sintese": {
            "hipoteses": [
                {"cid10": "D50.9", "nome": "Anemia por deficiência de ferro não especificada", "probabilidade": "alta", "justificativa": "Padrão laboratorial compatível.", "fonte": "SOP-CLIN-11"},
            ],
            "exames_sugeridos": [
                {"nome": "Pesquisa de sangue oculto nas fezes", "justificativa": "Rastrear perda digestiva.", "fonte": "SOP-CLIN-11"},
                {"nome": "Endoscopia e colonoscopia", "justificativa": "Investigar fonte de sangramento.", "fonte": "SOP-CLIN-11"},
            ],
            "medicacoes_sugeridas": [
                {"nome": "Sulfato ferroso", "dose": "conforme prescrição", "frequencia": "diária", "NOTA": "VALIDAÇÃO OBRIGATÓRIA"},
            ],
            "observacoes": "Repor ferro sem investigar a causa pode atrasar diagnóstico de neoplasia digestiva.",
        },
    },
]

MODELOS_VAL = [
    {
        "pedido": "Gere o modelo de laudo de ultrassonografia abdominal sem alterações.",
        "documento": """LAUDO DE ULTRASSONOGRAFIA ABDOMINAL TOTAL

Paciente: [NOME DO PACIENTE]        Idade: [IDADE]
Data do exame: [DATA]        Indicação: [INDICAÇÃO]

ACHADOS:
- Fígado de dimensões normais, contornos regulares e ecotextura homogênea.
- Vesícula biliar sem cálculos, paredes finas.
- Vias biliares sem dilatação.
- Pâncreas e baço sem alterações.
- Rins tópicos, com relação córtico-medular preservada, sem cálculos.
- Ausência de líquido livre na cavidade.

CONCLUSÃO: exame dentro dos limites da normalidade.

_______________________________
[NOME DO MÉDICO] — CRM [NÚMERO]

⚕️ Documento gerado com apoio de IA. Exige validação e assinatura do médico.""",
    },
    {
        "pedido": "Gere o modelo de receita para antibiótico de uso oral por 7 dias.",
        "documento": """RECEITUÁRIO SIMPLES

Paciente: [NOME DO PACIENTE]
Data: [DATA]

1. [ANTIBIÓTICO] [CONCENTRAÇÃO] ......................... [QUANTIDADE]
   Tomar 1 comprimido por via oral a cada [INTERVALO], por 7 dias.
   Tomar sempre no mesmo horário e completar o tratamento.

Orientações: não interromper antes do prazo, mesmo com melhora dos sintomas.
Retornar se houver piora, febre persistente ou reação alérgica.

_______________________________
[NOME DO MÉDICO] — CRM [NÚMERO]

⚕️ Documento gerado com apoio de IA. Exige validação e assinatura do médico.""",
    },
]
