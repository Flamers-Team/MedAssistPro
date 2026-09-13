# Infraestrutura — MedAssistPro

Máquina com GPU na AWS para treinar o modelo e rodar a demonstração.

## O que é criado

| Recurso | Para quê |
|---|---|
| Instância `g6.xlarge` | GPU L4 de 24 GB, onde o modelo treina e roda |
| Disco de 100 GB | Guarda modelo base, datasets e índice do RAG |
| IP fixo + `medassist.ia4.dev` | Endereço que não muda entre desligamentos |
| Grupo de segurança | Portas 80 e 443. Nenhuma porta de SSH |
| Papel do Session Manager | Terminal sem chave e sem porta aberta |
| Alarme de ociosidade | Desliga sozinha após 30 min de CPU baixa |

A imagem é a Deep Learning da AWS, que já traz driver Nvidia, CUDA e PyTorch.

## Criar (uma vez)

```bash
cd infra
terraform init
terraform apply
```

## Preparar a máquina

Instala tudo que a aplicação precisa: Node, ambiente Python com o PyTorch da
imagem, código do projeto, arquivos do Git LFS, interface compilada, Caddy,
serviço da API e o modelo.

```bash
./medassist.sh preparar --indexar --treinar
```

| Opção | O que faz | Tempo |
|---|---|---|
| (nenhuma) | Sobe a aplicação com o adapter publicado | ~10 min |
| `--indexar` | Constrói o índice do RAG com 10 mil bulas | +10 min |
| `--treinar` | Treina o adapter com os dados internos e usa esse | +5 min |
| `--mock` | Não baixa modelo: respostas sintéticas | ~8 min |

O script é idempotente: pode rodar de novo. Para o antes e depois do
fine-tuning, rode sem `--treinar`, teste, e depois com `--treinar`.

## Uso no dia a dia

```bash
./medassist.sh status      # estado, IP e endereço
./medassist.sh ligar       # liga e espera ficar pronta
./medassist.sh desligar    # desliga: para a cobrança por hora
./medassist.sh conectar    # terminal dentro da máquina
```

## Custo

| Situação | Custo |
|---|---|
| Ligada | Cerca de US$ 0,80 por hora |
| Desligada | Só o disco e o IP, cerca de US$ 12 por mês |
| Destruída | Zero |

Desligue sempre ao terminar. O alarme de ociosidade é rede de proteção, não substituto.

## Acesso

O terminal é pelo Session Manager, que exige login no SSO da AWS. O site em
`medassist.ia4.dev` é público e usa o login do próprio assistente.

Para restringir o site a um IP: `./medassist.sh acesso 189.1.2.3/32`.
Para liberar de novo: `./medassist.sh publico`.

## Apagar tudo no fim do projeto

```bash
cd infra && terraform destroy
```

Isso apaga a máquina e o disco. O que precisar guardar, como o adapter treinado,
deve estar publicado no HuggingFace antes.
