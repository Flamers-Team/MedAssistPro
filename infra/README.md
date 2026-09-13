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

```bash
./medassist.sh --preparar --indexar-rag --treinar
```

| Opção | O que faz | Tempo |
|---|---|---|
| `--preparar` | Pacotes, Node, Caddy, código, Git LFS, ambiente Python, interface, serviço da API e modelo | ~10 min |
| `--indexar-rag` | Índice do RAG com 10 mil bulas | +10 min |
| `--treinar` | Gera o dataset interno, anonimiza, treina o adapter e passa a usá-lo | +5 min |

O script é idempotente. Para comparar o antes e o depois do fine-tuning, rode
sem `--treinar`, teste o site, e depois rode com `--treinar`.

## Uso no dia a dia

```bash
./medassist.sh                 # mostra todas as opções
./medassist.sh --status        # estado, endereço e IP
./medassist.sh --ligar         # liga
./medassist.sh --desligar      # desliga: para a cobrança por hora
./medassist.sh --conectar      # terminal dentro da máquina
./medassist.sh --logs          # logs da API
./medassist.sh --ativar-mock   # site responde sem GPU, com texto sintético
./medassist.sh --ativar-gpu    # site responde com o modelo real
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

Quem pode abrir o site é uma regra única, sempre substituída:

- `./medassist.sh --ip` restringe ao IP de quem rodou o comando.
- `./medassist.sh --ip 200.1.2.0/24` restringe às faixas informadas.
- `./medassist.sh --publico` libera para a internet inteira.

A preparação já fecha o site no seu IP. Para a demonstração, rode `--publico`.

## Apagar tudo no fim do projeto

```bash
cd infra && terraform destroy
```

Isso apaga a máquina e o disco. O que precisar guardar, como o adapter treinado,
deve estar publicado no HuggingFace antes.
