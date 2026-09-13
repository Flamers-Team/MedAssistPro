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
| `--indexar-rag` | Índice do RAG com 10 mil bulas | ~10 min |
| `--treinar` | Gera o dataset interno, anonimiza, treina o adapter e passa a usá-lo | ~5 min |

O primeiro `--ligar` já roda a preparação sozinho. As duas etapas extras rodam
isoladamente, em momentos distintos, e falham se a máquina não estiver
preparada, em vez de instalar por conta própria.

Para o antes e depois do fine-tuning: indexe o RAG, grave com o adapter
publicado, rode `--treinar` e grave de novo.

## Uso no dia a dia

```bash
./medassist.sh                 # mostra todas as opções
./medassist.sh --status        # estado, endereço e IP
./medassist.sh --ligar         # liga
./medassist.sh --desligar      # desliga: para a cobrança por hora
./medassist.sh --conectar      # terminal dentro da máquina
./medassist.sh --logs          # logs da API
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

- `./medassist.sh --liberar-ip` restringe ao IP de quem rodou o comando.
- `./medassist.sh --liberar-ip 200.1.2.0/24` restringe às faixas informadas.
- `./medassist.sh --liberar-publico` libera para a internet inteira.

A preparação e o `--ligar` não mexem nessa regra: quem pode abrir o site é decisão
separada, tomada só por `--ip` e `--publico`.

## Apagar tudo no fim do projeto

```bash
cd infra && terraform destroy
```

Isso apaga a máquina e o disco. O que precisar guardar, como o adapter treinado,
deve estar publicado no HuggingFace antes.
