"""Perguntas frequentes de médicos, escritas como exemplos de SÍNTESE clínica.

Conteúdo sintético, criado para o Tech Challenge. Não é material institucional
real e não passou por validação clínica. Cada item vira um exemplo de treino no
mesmo formato que o agente de síntese usa: relato, histórico do paciente e
trechos recuperados na entrada, JSON estrito na saída, sempre com fonte citada.
"""

DUVIDAS = [
    {
        "relato": "Paciente de 61 anos, hipertenso e diabético, com dor torácica ao esforço há 3 dias e sudorese.",
        "historico": {
            "condicoes_cronicas": ["Hipertensão arterial", "Diabetes tipo 2"],
            "alergias": [],
            "historico": [
                {"data": "2026-01-20", "motivo": "Dor torácica ao esforço", "diagnostico": "Angina estável", "medicacoes": ["AAS 100mg", "Atorvastatina 40mg"]},
            ],
        },
        "rag": [
            "[Fonte: SOP-CARDIO-01] Dor torácica de características anginosas exige ECG em até 10 minutos e dosagem seriada de troponina.",
            "[Fonte: chatbulario] AAS: antiagregante plaquetário, indicado na doença arterial coronariana.",
        ],
        "sintese": {
            "hipoteses": [
                {"cid10": "I20.9", "nome": "Angina pectoris", "probabilidade": "alta", "justificativa": "Dor aos esforços em paciente com angina prévia e fatores de risco.", "fonte": "SOP-CARDIO-01"},
                {"cid10": "I21.9", "nome": "Infarto agudo do miocárdio", "probabilidade": "media", "justificativa": "Sudorese associada exige descartar evento agudo.", "fonte": "SOP-CARDIO-01"},
            ],
            "exames_sugeridos": [
                {"nome": "Eletrocardiograma", "justificativa": "Primeira avaliação de isquemia, em até 10 minutos.", "fonte": "SOP-CARDIO-01"},
                {"nome": "Troponina seriada", "justificativa": "Descartar necrose miocárdica.", "fonte": "SOP-CARDIO-01"},
            ],
            "medicacoes_sugeridas": [
                {"nome": "AAS", "dose": "100 mg", "frequencia": "1x ao dia", "NOTA": "VALIDAÇÃO OBRIGATÓRIA"},
            ],
            "observacoes": "Paciente já em uso de antiagregante. Manter monitorização até o resultado dos exames.",
        },
    },
    {
        "relato": "Paciente de 78 anos com pneumonia adquirida na comunidade e creatinina de 2,1. Qual antibiótico e qual ajuste de dose?",
        "historico": {
            "condicoes_cronicas": ["Doença renal crônica estágio 3"],
            "alergias": ["Penicilina (rash)"],
            "historico": [],
        },
        "rag": [
            "[Fonte: SOP-INFECTO-04] Pneumonia comunitária em idoso: considerar internação pelo escore de gravidade e ajustar antimicrobianos à função renal.",
            "[Fonte: chatbulario] Levofloxacino: ajustar intervalo quando clearance de creatinina abaixo de 50 mL/min.",
        ],
        "sintese": {
            "hipoteses": [
                {"cid10": "J18.9", "nome": "Pneumonia não especificada", "probabilidade": "alta", "justificativa": "Quadro respiratório em idoso com achados compatíveis.", "fonte": "SOP-INFECTO-04"},
            ],
            "exames_sugeridos": [
                {"nome": "Radiografia de tórax", "justificativa": "Confirmar consolidação e extensão.", "fonte": "SOP-INFECTO-04"},
                {"nome": "Função renal e eletrólitos", "justificativa": "Guiar o ajuste de dose.", "fonte": "SOP-INFECTO-04"},
            ],
            "medicacoes_sugeridas": [
                {"nome": "Levofloxacino", "dose": "750 mg no primeiro dia, depois conforme clearance", "frequencia": "intervalo ajustado à função renal", "NOTA": "VALIDAÇÃO OBRIGATÓRIA"},
            ],
            "observacoes": "Alergia a penicilina relatada: evitar betalactâmicos sem avaliação. Ajuste de dose obrigatório pela creatinina de 2,1.",
        },
    },
    {
        "relato": "Mulher de 34 anos com cefaleia recorrente, sem sinais de alerta. Preciso pedir tomografia?",
        "historico": {
            "condicoes_cronicas": [],
            "alergias": ["Dipirona (rash cutâneo leve)"],
            "historico": [
                {"data": "2025-11-02", "motivo": "Cefaleia tensional recorrente", "diagnostico": "Cefaleia tensional", "medicacoes": ["Paracetamol 750mg"]},
            ],
        },
        "rag": [
            "[Fonte: SOP-NEURO-02] Neuroimagem na cefaleia não é indicada de rotina na ausência de sinais de alerta.",
            "[Fonte: chatbulario] Paracetamol: analgésico e antitérmico, dose usual de 500 a 750 mg por tomada em adultos.",
        ],
        "sintese": {
            "hipoteses": [
                {"cid10": "G44.2", "nome": "Cefaleia do tipo tensional", "probabilidade": "alta", "justificativa": "Padrão recorrente já documentado, sem sinais de alarme.", "fonte": "SOP-NEURO-02"},
            ],
            "exames_sugeridos": [
                {"nome": "Nenhum exame de imagem de rotina", "justificativa": "Sem sinais de alerta, a neuroimagem não altera conduta.", "fonte": "SOP-NEURO-02"},
            ],
            "medicacoes_sugeridas": [
                {"nome": "Paracetamol", "dose": "750 mg", "frequencia": "até 3x ao dia, se dor", "NOTA": "VALIDAÇÃO OBRIGATÓRIA"},
            ],
            "observacoes": "Alergia a dipirona registrada: evitar. Reavaliar se houver mudança de padrão, despertar noturno ou déficit neurológico.",
        },
    },
    {
        "relato": "Paciente de 55 anos com diabetes tipo 2 e hemoglobina glicada de 9,2 em uso de metformina isolada. Qual o próximo passo?",
        "historico": {
            "condicoes_cronicas": ["Diabetes tipo 2", "Obesidade"],
            "alergias": [],
            "historico": [
                {"data": "2026-02-10", "motivo": "Controle de diabetes", "diagnostico": "Diabetes tipo 2 descompensado", "medicacoes": ["Metformina 850mg"]},
            ],
        },
        "rag": [
            "[Fonte: SOP-ENDO-03] Hemoglobina glicada acima da meta em monoterapia indica associação de segunda droga, orientada por comorbidades e peso.",
            "[Fonte: chatbulario] Metformina: primeira linha no diabetes tipo 2, com ajuste conforme função renal.",
        ],
        "sintese": {
            "hipoteses": [
                {"cid10": "E11.9", "nome": "Diabetes mellitus tipo 2 sem complicações", "probabilidade": "alta", "justificativa": "Controle glicêmico fora da meta em monoterapia.", "fonte": "SOP-ENDO-03"},
            ],
            "exames_sugeridos": [
                {"nome": "Função renal com taxa de filtração glomerular", "justificativa": "Definir segurança das opções terapêuticas.", "fonte": "SOP-ENDO-03"},
                {"nome": "Perfil lipídico e microalbuminúria", "justificativa": "Rastreio de complicações crônicas.", "fonte": "SOP-ENDO-03"},
            ],
            "medicacoes_sugeridas": [
                {"nome": "Associação de segunda droga antidiabética", "dose": "conforme escolha e função renal", "frequencia": "diária", "NOTA": "VALIDAÇÃO OBRIGATÓRIA"},
            ],
            "observacoes": "Reforçar adesão e mudança de estilo de vida antes de considerar insulinização.",
        },
    },
    {
        "relato": "Homem de 45 anos com infecção urinária de repetição, terceira no ano. Investigo ou trato de novo?",
        "historico": {"condicoes_cronicas": [], "alergias": [], "historico": []},
        "rag": [
            "[Fonte: SOP-URO-01] Infecção urinária de repetição em homem exige investigação do trato urinário e urocultura antes do antibiótico.",
        ],
        "sintese": {
            "hipoteses": [
                {"cid10": "N39.0", "nome": "Infecção do trato urinário de localização não especificada", "probabilidade": "alta", "justificativa": "Terceiro episódio no ano.", "fonte": "SOP-URO-01"},
                {"cid10": "N40", "nome": "Hiperplasia da próstata", "probabilidade": "baixa", "justificativa": "Causa possível de retenção e recorrência.", "fonte": "SOP-URO-01"},
            ],
            "exames_sugeridos": [
                {"nome": "Urocultura com antibiograma", "justificativa": "Guiar o antibiótico e documentar recorrência.", "fonte": "SOP-URO-01"},
                {"nome": "Ultrassonografia de rins e vias urinárias", "justificativa": "Investigar fator anatômico ou obstrutivo.", "fonte": "SOP-URO-01"},
            ],
            "medicacoes_sugeridas": [],
            "observacoes": "Recorrência em homem não é considerada simples: investigar antes de repetir o tratamento empírico.",
        },
    },
    {
        "relato": "Paciente de 68 anos internado, acamado, sem profilaxia prescrita. Devo iniciar profilaxia de trombose?",
        "historico": {"condicoes_cronicas": ["Insuficiência cardíaca"], "alergias": [], "historico": []},
        "rag": [
            "[Fonte: SOP-CLIN-07] Todo paciente clínico internado deve ter risco de tromboembolismo avaliado na admissão e a cada 48 horas.",
        ],
        "sintese": {
            "hipoteses": [
                {"cid10": "Z29.2", "nome": "Necessidade de profilaxia", "probabilidade": "alta", "justificativa": "Paciente clínico acamado com fator de risco adicional.", "fonte": "SOP-CLIN-07"},
            ],
            "exames_sugeridos": [
                {"nome": "Hemograma e função renal", "justificativa": "Definir dose e segurança da profilaxia.", "fonte": "SOP-CLIN-07"},
            ],
            "medicacoes_sugeridas": [
                {"nome": "Heparina de baixo peso molecular em dose profilática", "dose": "conforme peso e função renal", "frequencia": "1x ao dia", "NOTA": "VALIDAÇÃO OBRIGATÓRIA"},
            ],
            "observacoes": "Avaliar contraindicações e risco de sangramento antes de iniciar.",
        },
    },
    {
        "relato": "Mulher de 62 anos com hipotireoidismo em uso de levotiroxina, com TSH ainda elevado. Como ajusto?",
        "historico": {
            "condicoes_cronicas": ["Hipotireoidismo"],
            "alergias": [],
            "historico": [
                {"data": "2026-04-02", "motivo": "Revisão de tireoide", "diagnostico": "Hipotireoidismo em ajuste", "medicacoes": ["Levotiroxina 75mcg"]},
            ],
        },
        "rag": [
            "[Fonte: SOP-ENDO-05] Ajustes de levotiroxina devem respeitar intervalo mínimo de 6 semanas entre dosagens de TSH.",
            "[Fonte: chatbulario] Levotiroxina: tomar em jejum, com intervalo para outros medicamentos e alimentos.",
        ],
        "sintese": {
            "hipoteses": [
                {"cid10": "E03.9", "nome": "Hipotireoidismo não especificado", "probabilidade": "alta", "justificativa": "TSH acima da meta em uso de reposição.", "fonte": "SOP-ENDO-05"},
            ],
            "exames_sugeridos": [
                {"nome": "TSH e T4 livre em 6 a 8 semanas", "justificativa": "Avaliar resposta ao ajuste.", "fonte": "SOP-ENDO-05"},
            ],
            "medicacoes_sugeridas": [
                {"nome": "Levotiroxina", "dose": "ajuste da dose atual conforme TSH", "frequencia": "1x ao dia em jejum", "NOTA": "VALIDAÇÃO OBRIGATÓRIA"},
            ],
            "observacoes": "Confirmar adesão e forma de uso antes de aumentar a dose, pois erro de administração é causa comum de TSH persistente.",
        },
    },
    {
        "relato": "Paciente de 29 anos com crise de asma frequente, usando bombinha de resgate quase todo dia. O que revisar?",
        "historico": {"condicoes_cronicas": ["Asma"], "alergias": [], "historico": []},
        "rag": [
            "[Fonte: SOP-PNEUMO-02] Uso de resgate mais de duas vezes por semana indica controle inadequado e revisão da terapia de manutenção.",
        ],
        "sintese": {
            "hipoteses": [
                {"cid10": "J45.9", "nome": "Asma não especificada", "probabilidade": "alta", "justificativa": "Sintomas frequentes com uso diário de resgate.", "fonte": "SOP-PNEUMO-02"},
            ],
            "exames_sugeridos": [
                {"nome": "Espirometria", "justificativa": "Documentar obstrução e resposta ao broncodilatador.", "fonte": "SOP-PNEUMO-02"},
            ],
            "medicacoes_sugeridas": [
                {"nome": "Corticoide inalatório de manutenção", "dose": "conforme etapa de tratamento", "frequencia": "diária", "NOTA": "VALIDAÇÃO OBRIGATÓRIA"},
            ],
            "observacoes": "Revisar técnica inalatória e gatilhos ambientais antes de escalonar a dose.",
        },
    },
    {
        "relato": "Homem de 50 anos com achado de nódulo pulmonar de 7 milímetros em tomografia feita por outro motivo. Como conduzir?",
        "historico": {"condicoes_cronicas": [], "alergias": [], "historico": []},
        "rag": [
            "[Fonte: SOP-PNEUMO-06] Nódulo pulmonar sólido menor que 8 milímetros em paciente de risco habitual: seguimento por imagem, sem biópsia imediata.",
        ],
        "sintese": {
            "hipoteses": [
                {"cid10": "R91.1", "nome": "Nódulo pulmonar solitário", "probabilidade": "alta", "justificativa": "Achado incidental compatível com nódulo subcentimétrico.", "fonte": "SOP-PNEUMO-06"},
            ],
            "exames_sugeridos": [
                {"nome": "Tomografia de controle em 6 a 12 meses", "justificativa": "Acompanhar estabilidade do nódulo.", "fonte": "SOP-PNEUMO-06"},
            ],
            "medicacoes_sugeridas": [],
            "observacoes": "Estratificar risco pelo histórico de tabagismo e características do nódulo antes de definir o intervalo.",
        },
    },
    {
        "relato": "Paciente de 71 anos em uso de varfarina com INR de 6,5, sem sangramento. Como proceder?",
        "historico": {"condicoes_cronicas": ["Fibrilação atrial"], "alergias": [], "historico": []},
        "rag": [
            "[Fonte: SOP-HEMO-03] INR muito elevado sem sangramento: suspender a dose, reavaliar em 24 horas e investigar interação medicamentosa.",
            "[Fonte: chatbulario] Varfarina: numerosas interações com antibióticos e anti-inflamatórios, exigindo controle de INR.",
        ],
        "sintese": {
            "hipoteses": [
                {"cid10": "D68.3", "nome": "Transtorno hemorrágico por anticoagulante", "probabilidade": "alta", "justificativa": "INR muito acima da faixa terapêutica.", "fonte": "SOP-HEMO-03"},
            ],
            "exames_sugeridos": [
                {"nome": "Repetir INR em 24 horas", "justificativa": "Acompanhar a queda após suspensão.", "fonte": "SOP-HEMO-03"},
                {"nome": "Hemograma", "justificativa": "Avaliar sinais de sangramento oculto.", "fonte": "SOP-HEMO-03"},
            ],
            "medicacoes_sugeridas": [
                {"nome": "Suspensão temporária da varfarina", "dose": "suspender", "frequencia": "reavaliar em 24 horas", "NOTA": "VALIDAÇÃO OBRIGATÓRIA"},
            ],
            "observacoes": "Revisar medicamentos iniciados recentemente, principalmente antibióticos, como causa da elevação.",
        },
    },
]
