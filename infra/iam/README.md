# Papel da esteira do GitHub

A esteira **não cria nem destrói infraestrutura**. Ela só opera: liga, desliga,
prepara, indexa, treina, troca o modelo e muda quem pode abrir o site.

Criar e destruir continua sendo feito com o seu usuário, rodando Terraform.

## O que o papel permite

| Permissão | Para quê | Limite |
|---|---|---|
| `ec2:Describe*`, `ssm:Describe*`, `ssm:GetCommandInvocation` | ver o estado do ambiente | leitura |
| `ec2:StartInstances`, `StopInstances` | ligar e desligar | só recursos com a etiqueta `Projeto=MedAssistPro` |
| `ec2:AuthorizeSecurityGroupIngress`, `RevokeSecurityGroupIngress` | abrir e fechar o site | só o grupo do projeto |
| `ssm:SendCommand` | rodar preparar, indexar, treinar e trocar o modelo | só a instância do projeto |

Não há permissão para criar, destruir, redimensionar nem acessar dados de
outros serviços.

## Como criar (uma vez, com o seu usuário)

```bash
export AWS_PROFILE=selvs

aws iam create-role \
  --role-name medassist-esteira \
  --assume-role-policy-document file://infra/iam/confianca-github.json

aws iam put-role-policy \
  --role-name medassist-esteira \
  --policy-name medassist-operar \
  --policy-document file://infra/iam/permissoes-esteira.json

aws iam get-role --role-name medassist-esteira --query Role.Arn --output text
```

Depois, no GitHub, em Settings → Secrets and variables → Actions → Variables,
crie a variável `AWS_ROLE_ARN` com o valor devolvido pelo último comando.

## Como usar

Actions → MedAssist → Run workflow. Escolha a ação e, quando for o caso,
preencha o campo `valor`:

| Ação | Campo `valor` |
|---|---|
| `modelo` | `biomistral-medquad-lora` ou `biomistral-medassist-lora` |
| `liberar-ip` | `189.1.2.3/32`. Vazio usa o IP do runner do GitHub |
| demais | vazio |

Toda execução termina escrevendo no resumo a posição do ambiente: instância,
estado, endereço, IP fixo, modelo em uso e quem pode abrir o site.
