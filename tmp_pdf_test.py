from src.docs.generator import DocumentGenerator

dados = {
    'paciente': 'Maria Silva',
    'idade': 45,
    'sexo': 'F',
    'medico': 'Dr. João',
    'crm': '12345-SP',
    'queixa_principal': 'Dor torácica, sudorese e ansiedade.',
    'exame_fisico': 'Conforme avaliação clínica.',
    'hipoteses': [{'cid10': 'I20', 'nome': 'Angina', 'probabilidade': 'media', 'justificativa': 'Teste', 'fonte': 'MOCK'}],
    'exames_sugeridos': [{'nome': 'ECG', 'justificativa': 'teste', 'fonte': 'MOCK'}],
    'medicacoes_sugeridas': [{'nome': 'Aspirina', 'dose': '100mg', 'frequencia': '1x/dia', 'NOTA': 'VALIDAÇÃO MÉDICA OBRIGATÓRIA'}],
    'observacoes': 'Teste',
}

g = DocumentGenerator(output_dir='data/documents')
print(g.gerar_prontuario(dados))
