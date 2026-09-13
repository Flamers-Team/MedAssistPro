#!/usr/bin/env bash
# Controle da máquina do MedAssistPro na AWS.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export AWS_PROFILE="${AWS_PROFILE:-selvs}"
REGIAO="${AWS_REGION:-us-east-1}"

ajuda() {
  cat <<'AJUDA'
MedAssistPro — controle da máquina com GPU na AWS

  ./medassist.sh [opções]

A máquina precisa existir antes: cd infra && terraform apply

MÁQUINA
  --status          estado atual, endereço e IP fixo
  --ligar           liga e espera ficar pronta. Na primeira vez, roda a
                    preparação sozinho
  --desligar        desliga. Preserva disco e IP, e para a cobrança por hora
  --conectar        abre um terminal dentro da máquina (Session Manager)
  --logs            últimas linhas do serviço da API

INSTALAÇÃO
  As duas últimas exigem uma máquina já preparada e rodam isoladamente, em
  momentos distintos. Se ela não estiver preparada, falham em vez de instalar.

  --preparar        instala e configura tudo: pacotes, Node, Caddy, código do
                    projeto, arquivos do Git LFS, ambiente Python, interface
                    compilada, serviço da API e download do modelo. Repetir não
                    quebra nada (~10 min)
  --indexar-rag     constrói o índice do RAG com 10 mil bulas (~10 min)
  --treinar         gera o dataset interno, anonimiza, treina o adapter e passa
                    a usar o modelo novo (~5 min)

QUEM PODE ABRIR O SITE
  Regra única, sempre substituída. Não é tocada por --ligar nem --preparar.

  --publico         libera para a internet inteira, apagando as regras de IP
  --ip [CIDR...]    libera só os IPs informados, apagando a regra pública e as
                    anteriores. Sem argumento, usa o IP de quem rodou o comando.
                    Ex.: --ip   ou   --ip 200.1.2.0/24

DIA A DIA
  ./medassist.sh --ligar          # máquina pronta e site no ar
  ./medassist.sh --status
  ./medassist.sh --desligar       # sempre, ao terminar

SEQUÊNCIA PARA GRAVAR O ANTES E O DEPOIS DO FINE-TUNING
  ./medassist.sh --ligar          # sobe com o adapter publicado
  ./medassist.sh --indexar-rag    # busca em bulas ativa, fora da gravação
  ... grave a consulta: é o ANTES
  ./medassist.sh --treinar        # 3 min, dá para filmar a perda caindo
  ... repita a mesma consulta: é o DEPOIS

Ligada custa cerca de US$ 0,80 por hora. Desligada, só disco e IP.
Usa o seu login do SSO. Se expirar: aws sso login --profile selvs
AJUDA
}

_id() {
  terraform -chdir="$DIR" output -raw instancia_id 2>/dev/null || {
    echo "Infraestrutura ainda não criada. Rode: terraform -chdir=$DIR apply" >&2
    exit 1
  }
}

# Roda comandos dentro da máquina e mostra a saída.
_remoto() {
  local descricao="$1"; shift
  local id; id="$(_id)"
  echo "$descricao"
  local cmd
  cmd=$(aws ssm send-command --region "$REGIAO" --instance-ids "$id" \
    --document-name "AWS-RunShellScript" --timeout-seconds 7200 \
    --parameters "commands=$1" --query "Command.CommandId" --output text)
  until aws ssm wait command-executed --command-id "$cmd" --instance-id "$id" --region "$REGIAO" 2>/dev/null; do
    local estado; estado=$(aws ssm get-command-invocation --command-id "$cmd" --instance-id "$id" --region "$REGIAO" --query "Status" --output text)
    echo "  ... $estado"
    [ "$estado" = "InProgress" ] || break
  done
  aws ssm get-command-invocation --command-id "$cmd" --instance-id "$id" --region "$REGIAO" \
    --query "StandardOutputContent" --output text | tail -40
}

# A máquina já passou pela preparação?
_preparada() {
  local id; id="$(_id)"
  local cmd
  cmd=$(aws ssm send-command --region "$REGIAO" --instance-ids "$id" \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=["test -f /etc/systemd/system/medassist-api.service && test -d /opt/medassist/app && echo sim || echo nao"]' \
    --query "Command.CommandId" --output text 2>/dev/null) || return 1
  aws ssm wait command-executed --command-id "$cmd" --instance-id "$id" --region "$REGIAO" 2>/dev/null || true
  [ "$(aws ssm get-command-invocation --command-id "$cmd" --instance-id "$id" --region "$REGIAO" --query 'StandardOutputContent' --output text 2>/dev/null | tr -d '[:space:]')" = "sim" ]
}

# Roda a preparação dentro da máquina. Não mexe em quem pode abrir o site:
# isso é assunto do --ip e do --publico.
_preparar() {
  local opcoes="${1:-}"
  local b64; b64=$(base64 -w0 "$DIR/preparar_maquina.sh")
  _remoto "Preparando a máquina$opcoes. Pode levar de 10 a 30 minutos." \
    "[\"echo $b64 | base64 -d > /root/preparar_maquina.sh\",\"chmod +x /root/preparar_maquina.sh\",\"/root/preparar_maquina.sh$opcoes\"]"
}

# IP público de quem está rodando o comando.
_meu_ip() {
  curl -s --max-time 10 https://checkip.amazonaws.com | tr -d '[:space:]'
}

# Grava a regra de acesso e aplica. Sempre substitui a regra anterior:
# rodar de novo com outro valor apaga o que existia antes (idempotente).
_regra_acesso() {
  local lista="$1" descricao="$2"
  echo "$descricao"
  printf 'ips_liberados = %s\n' "$lista" > "$DIR/acesso.auto.tfvars"
  terraform -chdir="$DIR" apply -auto-approve -var="ips_liberados=$lista" | tail -3
  echo "regra atual: $lista"
}

[ $# -eq 0 ] && { ajuda; exit 0; }

PREPARAR=0
EXTRAS=""
ACOES=()
IPS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --help|-h)      ajuda; exit 0 ;;
    --status|--ligar|--desligar|--conectar|--logs|--publico) ACOES+=("$1") ;;
    --preparar)     PREPARAR=1 ;;
    --indexar-rag)  EXTRAS="$EXTRAS --indexar-rag" ;;
    --treinar)      EXTRAS="$EXTRAS --treinar" ;;
    --ip)           shift; while [ $# -gt 0 ] && [[ "$1" != --* ]]; do IPS+=("$1"); shift; done; ACOES+=("--ip"); continue ;;
    *) echo "opção desconhecida: $1" >&2; echo; ajuda; exit 1 ;;
  esac
  shift
done

if [ "$PREPARAR" = "1" ]; then
  # Instalação completa, com as etapas extras no fim, se pedidas.
  _preparar "$EXTRAS"
elif [ -n "$EXTRAS" ]; then
  # Etapas extras sozinhas: exigem uma máquina já preparada.
  if ! _preparada; then
    echo "Erro: a máquina não está preparada, então$EXTRAS não pode rodar." >&2
    echo "Rode primeiro: ./medassist.sh --ligar   (liga e prepara)" >&2
    echo "Ou force a instalação: ./medassist.sh --preparar" >&2
    exit 1
  fi
  _preparar " --apenas$EXTRAS"
fi

for acao in ${ACOES[@]+"${ACOES[@]}"}; do
  case "$acao" in
    --status)
      echo "instância: $(_id)"
      echo "estado:    $(aws ec2 describe-instances --instance-ids "$(_id)" --region "$REGIAO" --query 'Reservations[0].Instances[0].State.Name' --output text)"
      echo "endereço:  $(terraform -chdir="$DIR" output -raw endereco 2>/dev/null || echo '-')"
      echo "ip fixo:   $(terraform -chdir="$DIR" output -raw ip_publico 2>/dev/null || echo '-')"
      ;;
    --ligar)
      ID="$(_id)"; echo "Ligando $ID..."
      aws ec2 start-instances --instance-ids "$ID" --region "$REGIAO" >/dev/null
      aws ec2 wait instance-running --instance-ids "$ID" --region "$REGIAO"
      aws ec2 wait instance-status-ok --instance-ids "$ID" --region "$REGIAO"
      if [ "$PREPARAR" = "0" ] && ! _preparada; then
        echo "Máquina ainda não preparada. Preparando agora..."
        _preparar ""
      fi
      echo "Pronta: $(terraform -chdir="$DIR" output -raw endereco)"
      echo "⚠️  Lembre de desligar ao terminar: ./medassist.sh --desligar"
      ;;
    --desligar)
      ID="$(_id)"; echo "Desligando $ID..."
      aws ec2 stop-instances --instance-ids "$ID" --region "$REGIAO" >/dev/null
      aws ec2 wait instance-stopped --instance-ids "$ID" --region "$REGIAO"
      echo "Desligada. Para de cobrar por hora; disco e IP continuam."
      ;;
    --conectar) aws ssm start-session --target "$(_id)" --region "$REGIAO" ;;
    --logs)     _remoto "Logs da API:" '["journalctl -u medassist-api -n 40 --no-pager"]' ;;
    --publico) _regra_acesso '["0.0.0.0/0"]' "Liberando o site para a internet inteira..." ;;
    --ip)
      if [ ${#IPS[@]} -eq 0 ]; then
        MEU_IP=$(_meu_ip)
        [ -n "$MEU_IP" ] || { echo "Não consegui descobrir seu IP. Informe manualmente: --ip 189.1.2.3/32" >&2; exit 1; }
        IPS=("$MEU_IP/32")
        echo "IP detectado: $MEU_IP"
      fi
      LISTA=$(printf '"%s",' "${IPS[@]}"); LISTA="[${LISTA%,}]"
      _regra_acesso "$LISTA" "Restringindo o site aos IPs informados..."
      ;;
  esac
done
