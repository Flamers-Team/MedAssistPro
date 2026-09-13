"""Protocolos internos do hospital, escritos como exemplos de TRIAGEM.

Conteúdo sintético, criado para o Tech Challenge. Não é protocolo institucional
real e não passou por validação clínica. Cada item vira um exemplo de treino no
mesmo formato que o agente de triagem usa em produção: relato na entrada,
JSON estrito na saída.
"""

PROTOCOLOS = [
    {
        "relato": "Homem de 58 anos, hipertenso, com dor retroesternal em aperto há 40 minutos, irradiando para o braço esquerdo, com sudorese fria e náusea.",
        "triagem": {
            "categoria": "EMERGENCIA",
            "justificativa": "Dor torácica típica com irradiação e sudorese: protocolo de dor torácica, ECG em até 10 minutos.",
            "red_flags": ["dor retroesternal em aperto", "irradiação para braço esquerdo", "sudorese fria"],
            "confianca": "alta",
        },
    },
    {
        "relato": "Mulher de 72 anos com fala arrastada e fraqueza no braço direito iniciadas há 1 hora, segundo a filha.",
        "triagem": {
            "categoria": "EMERGENCIA",
            "justificativa": "Déficit neurológico focal agudo dentro da janela: protocolo de AVC, tomografia imediata.",
            "red_flags": ["disartria", "hemiparesia direita", "início há menos de 4,5 horas"],
            "confianca": "alta",
        },
    },
    {
        "relato": "Homem de 34 anos com urticária difusa, edema de lábios e sensação de aperto na garganta 15 minutos após tomar dipirona.",
        "triagem": {
            "categoria": "EMERGENCIA",
            "justificativa": "Anafilaxia com acometimento de via aérea após exposição a fármaco: adrenalina intramuscular imediata.",
            "red_flags": ["edema de lábios", "aperto na garganta", "exposição recente a fármaco"],
            "confianca": "alta",
        },
    },
    {
        "relato": "Paciente de 66 anos, diabético, com febre de 39 graus, confusão mental, frequência respiratória de 28 e pressão arterial 85 por 50.",
        "triagem": {
            "categoria": "EMERGENCIA",
            "justificativa": "Sinais de sepse com hipotensão: protocolo de sepse, coleta de culturas e antibiótico na primeira hora.",
            "red_flags": ["hipotensão", "confusão mental", "taquipneia", "febre alta"],
            "confianca": "alta",
        },
    },
    {
        "relato": "Mulher de 28 anos, gestante de 32 semanas, com cefaleia intensa, visão turva e pressão arterial 165 por 110.",
        "triagem": {
            "categoria": "EMERGENCIA",
            "justificativa": "Suspeita de pré-eclâmpsia grave: avaliação obstétrica imediata e controle pressórico.",
            "red_flags": ["hipertensão grave na gestação", "cefaleia intensa", "alteração visual"],
            "confianca": "alta",
        },
    },
    {
        "relato": "Homem de 45 anos, etilista, com vômitos com sangue vivo há 2 horas e palidez importante.",
        "triagem": {
            "categoria": "EMERGENCIA",
            "justificativa": "Hemorragia digestiva alta com repercussão: acesso calibroso, reposição volêmica e endoscopia.",
            "red_flags": ["hematêmese", "palidez", "sangramento ativo"],
            "confianca": "alta",
        },
    },
    {
        "relato": "Paciente de 19 anos, diabético tipo 1, com poliúria, dor abdominal, respiração profunda e hálito cetônico há 1 dia.",
        "triagem": {
            "categoria": "EMERGENCIA",
            "justificativa": "Quadro compatível com cetoacidose diabética: hidratação, insulina e correção de eletrólitos.",
            "red_flags": ["respiração de Kussmaul", "hálito cetônico", "dor abdominal"],
            "confianca": "alta",
        },
    },
    {
        "relato": "Homem de 61 anos com dor torácica ao esforço há 3 dias, que melhora com repouso, sem dor no momento da consulta.",
        "triagem": {
            "categoria": "URGENTE",
            "justificativa": "Padrão sugestivo de angina estável: avaliação cardiológica e ECG ainda hoje, sem dor no momento.",
            "red_flags": ["dor aos esforços", "fatores de risco cardiovascular"],
            "confianca": "media",
        },
    },
    {
        "relato": "Mulher de 40 anos com febre de 38,5 graus, dor lombar à direita, disúria e náuseas há 2 dias.",
        "triagem": {
            "categoria": "URGENTE",
            "justificativa": "Suspeita de pielonefrite: exames, hidratação e antibiótico ainda nesta avaliação.",
            "red_flags": ["febre com dor lombar", "sintomas urinários"],
            "confianca": "alta",
        },
    },
    {
        "relato": "Homem de 52 anos com pressão arterial 190 por 120 aferida em casa, com cefaleia leve, sem déficit neurológico ou dor torácica.",
        "triagem": {
            "categoria": "URGENTE",
            "justificativa": "Urgência hipertensiva sem lesão de órgão-alvo: redução gradual e reavaliação, sem anti-hipertensivo endovenoso.",
            "red_flags": ["pressão arterial muito elevada"],
            "confianca": "media",
        },
    },
    {
        "relato": "Criança de 5 anos com tosse, febre de 38,8 graus há 3 dias, tiragem subcostal leve e saturação de 94 por cento.",
        "triagem": {
            "categoria": "URGENTE",
            "justificativa": "Pneumonia com esforço respiratório leve: radiografia, oxigenação e reavaliação em ambiente assistido.",
            "red_flags": ["tiragem subcostal", "saturação limítrofe"],
            "confianca": "media",
        },
    },
    {
        "relato": "Mulher de 35 anos com crise de asma, falando frases curtas, com sibilos difusos e saturação de 93 por cento.",
        "triagem": {
            "categoria": "URGENTE",
            "justificativa": "Crise asmática moderada: broncodilatador inalatório, corticoide sistêmico e reavaliação em 1 hora.",
            "red_flags": ["fala entrecortada", "sibilância difusa"],
            "confianca": "alta",
        },
    },
    {
        "relato": "Homem de 70 anos com dor em panturrilha direita, edema assimétrico e empastamento há 2 dias, após viagem longa.",
        "triagem": {
            "categoria": "URGENTE",
            "justificativa": "Suspeita de trombose venosa profunda: ultrassom com Doppler e avaliação de anticoagulação.",
            "red_flags": ["edema assimétrico", "imobilização prolongada"],
            "confianca": "media",
        },
    },
    {
        "relato": "Paciente de 26 anos com dor em fossa ilíaca direita há 12 horas, náusea, febre baixa e dor à descompressão.",
        "triagem": {
            "categoria": "URGENTE",
            "justificativa": "Abdome agudo com sinais de irritação peritoneal: avaliação cirúrgica e exames de imagem.",
            "red_flags": ["dor à descompressão", "migração da dor"],
            "confianca": "alta",
        },
    },
    {
        "relato": "Idoso de 80 anos com queda da própria altura, dor no quadril esquerdo e incapacidade de deambular, sem perda de consciência.",
        "triagem": {
            "categoria": "URGENTE",
            "justificativa": "Suspeita de fratura de fêmur proximal: radiografia, analgesia e avaliação ortopédica.",
            "red_flags": ["incapacidade de deambular", "trauma em idoso"],
            "confianca": "alta",
        },
    },
    {
        "relato": "Homem de 30 anos com dor de garganta há 3 dias, febre de 38 graus, sem dificuldade para engolir ou falta de ar.",
        "triagem": {
            "categoria": "ROTINA",
            "justificativa": "Faringite sem sinais de complicação: sintomáticos e reavaliação se piora.",
            "red_flags": [],
            "confianca": "alta",
        },
    },
    {
        "relato": "Mulher de 45 anos com dor lombar há 2 semanas após esforço, sem irradiação, sem febre e sem alteração urinária.",
        "triagem": {
            "categoria": "ROTINA",
            "justificativa": "Lombalgia mecânica sem sinais de alerta: analgesia, orientação e reavaliação ambulatorial.",
            "red_flags": [],
            "confianca": "alta",
        },
    },
    {
        "relato": "Paciente de 55 anos, hipertenso controlado, comparece para renovação de receita e resultado de exames de rotina.",
        "triagem": {
            "categoria": "ROTINA",
            "justificativa": "Consulta de acompanhamento de condição crônica estável, sem queixa aguda.",
            "red_flags": [],
            "confianca": "alta",
        },
    },
    {
        "relato": "Mulher de 24 anos com espirros, coriza clara e prurido nasal há 5 dias, sem febre, com histórico de rinite alérgica.",
        "triagem": {
            "categoria": "ROTINA",
            "justificativa": "Rinite alérgica em padrão habitual: tratamento sintomático e orientação sobre desencadeantes.",
            "red_flags": [],
            "confianca": "alta",
        },
    },
    {
        "relato": "Homem de 38 anos com dor de cabeça há 6 meses, duas vezes por semana, em aperto, sem sinais de alerta, buscando avaliação.",
        "triagem": {
            "categoria": "ROTINA",
            "justificativa": "Cefaleia tensional crônica sem sinais de alarme: investigação e acompanhamento ambulatorial.",
            "red_flags": [],
            "confianca": "media",
        },
    },
]
