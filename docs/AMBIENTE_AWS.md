# Ambiente na AWS — o que foi entregue

Máquina com GPU na AWS que treina o modelo e hospeda o assistente em
`https://medassist.ia4.dev`. Nada disso é exigido pelo enunciado: é a
infraestrutura que permite rodar e gravar a demonstração.

## Entregue

- [x] Infraestrutura como código, em `infra/` (Terraform): instância `g6.xlarge`
      com GPU L4, disco de 100 GB, IP fixo, registro no Route 53, papel do
      Session Manager e alarme que desliga por ociosidade
- [x] Acesso ao terminal sem SSH e sem chave, pelo Session Manager
- [x] Preparação reproduzível da máquina, em `infra/preparar_maquina.sh`:
      pacotes, Node, Caddy, código do projeto, arquivos do Git LFS, ambiente
      Python, interface compilada, serviço da API e download do modelo
- [x] Script de operação `infra/medassist.sh`, com onze opções e ajuda
- [x] Esteira no GitHub, em `.github/workflows/medassist.yml`, com as mesmas
      ações, autenticação por OIDC e resumo do ambiente a cada execução
- [x] Papel da esteira limitado por etiqueta do projeto, em `infra/iam/`:
      opera, mas não cria nem destrói nada
- [x] HTTPS com certificado automático, servido pelo Caddy no mesmo endereço
      da interface
- [x] Conferência estática dos scripts, em `infra/verificar.sh`
- [x] Teste do zero validado: ambiente destruído e recriado, com preparação,
      indexação do RAG e treino rodando pela esteira

## Como usar

```bash
cd infra && terraform apply     # cria a máquina (uma vez, com usuário admin)
./medassist.sh --ligar          # liga e, na primeira vez, prepara
./medassist.sh --indexar-rag    # índice do RAG com 10 mil bulas
./medassist.sh --treinar        # treina com os dados internos
./medassist.sh --desligar       # sempre, ao terminar
```

Pelo GitHub: aba Actions, fluxo MedAssist, botão Run workflow.

Detalhes em [`infra/README.md`](../infra/README.md) e
[`infra/iam/README.md`](../infra/iam/README.md).

## Custo

| Situação | Custo |
|---|---|
| Ligada | US$ 0,80 por hora |
| Desligada | cerca de US$ 0,39 por dia (disco e IP) |
| Destruída | zero |

Referência do dia 13/09/2026, com 4,9 horas ligadas em duas máquinas, incluindo
o teste de destruir e recriar: **US$ 4,05**.

## Limites conhecidos

- O certificado exige acesso público na primeira emissão: uma máquina nova
  precisa de `--liberar-publico` até o certificado sair, e só então pode ser
  restringida.
- A esteira pode rodar comandos dentro da máquina, então quem tem acesso de
  escrita ao repositório opera o ambiente. O limite é a política na AWS.
- O adapter treinado vive no disco da máquina. Destruir a máquina apaga o
  arquivo, e recriá-lo custa cerca de 8 minutos de treino.
