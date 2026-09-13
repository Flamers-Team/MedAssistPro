#!/usr/bin/env bash
# Controle da máquina do MedAssistPro na AWS.
#
#   ./medassist.sh status      estado atual, IP e endereço
#   ./medassist.sh ligar       liga e espera ficar pronta
#   ./medassist.sh desligar    desliga (o disco e o IP são preservados)
#   ./medassist.sh conectar    abre o terminal pelo Session Manager
#   ./medassist.sh acesso ...  quem pode abrir o site (CIDR), ex.: acesso 189.1.2.3/32
#   ./medassist.sh publico     libera o site para a internet
#   ./medassist.sh preparar    instala e configura tudo na máquina (aceita --indexar, --treinar, --mock)
#   ./medassist.sh logs        últimas linhas do serviço da API
#
# Usa o seu login do SSO. Se expirar: aws sso login --profile selvs
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export AWS_PROFILE="${AWS_PROFILE:-selvs}"
REGIAO="${AWS_REGION:-us-east-1}"

_id() {
  terraform -chdir="$DIR" output -raw instancia_id 2>/dev/null || {
    echo "Infraestrutura ainda não criada. Rode: terraform -chdir=$DIR apply" >&2
    exit 1
  }
}

_estado() {
  aws ec2 describe-instances --instance-ids "$(_id)" --region "$REGIAO" \
    --query "Reservations[0].Instances[0].State.Name" --output text
}

case "${1:-status}" in
  status)
    ID="$(_id)"
    echo "instância: $ID"
    echo "estado:    $(_estado)"
    echo "endereço:  $(terraform -chdir="$DIR" output -raw endereco 2>/dev/null || echo '-')"
    echo "ip fixo:   $(terraform -chdir="$DIR" output -raw ip_publico 2>/dev/null || echo '-')"
    ;;

  ligar)
    ID="$(_id)"
    echo "Ligando $ID..."
    aws ec2 start-instances --instance-ids "$ID" --region "$REGIAO" >/dev/null
    aws ec2 wait instance-running --instance-ids "$ID" --region "$REGIAO"
    echo "Instância no ar. Aguardando o sistema responder..."
    aws ec2 wait instance-status-ok --instance-ids "$ID" --region "$REGIAO"
    echo "Pronta: $(terraform -chdir="$DIR" output -raw endereco)"
    echo "⚠️  Lembre de desligar ao terminar: ./medassist.sh desligar"
    ;;

  desligar)
    ID="$(_id)"
    echo "Desligando $ID..."
    aws ec2 stop-instances --instance-ids "$ID" --region "$REGIAO" >/dev/null
    aws ec2 wait instance-stopped --instance-ids "$ID" --region "$REGIAO"
    echo "Desligada. Para de cobrar por hora; disco e IP continuam."
    ;;

  conectar)
    aws ssm start-session --target "$(_id)" --region "$REGIAO"
    ;;

  preparar)
    shift
    ID="$(_id)"
    echo "Enviando a preparação para $ID. Pode levar de 10 a 40 minutos, conforme as opções."
    B64=$(base64 -w0 "$DIR/preparar_maquina.sh")
    CMD=$(aws ssm send-command --region "$REGIAO" --instance-ids "$ID" \
      --document-name "AWS-RunShellScript" --timeout-seconds 7200 \
      --parameters "commands=[\"echo $B64 | base64 -d > /root/preparar_maquina.sh\",\"chmod +x /root/preparar_maquina.sh\",\"/root/preparar_maquina.sh $*\"]" \
      --query "Command.CommandId" --output text)
    echo "comando: $CMD"
    until aws ssm wait command-executed --command-id "$CMD" --instance-id "$ID" --region "$REGIAO" 2>/dev/null; do
      ESTADO=$(aws ssm get-command-invocation --command-id "$CMD" --instance-id "$ID" --region "$REGIAO" --query "Status" --output text)
      echo "  ... $ESTADO"
      [ "$ESTADO" = "InProgress" ] || break
    done
    aws ssm get-command-invocation --command-id "$CMD" --instance-id "$ID" --region "$REGIAO" \
      --query "StandardOutputContent" --output text | tail -40
    ;;

  logs)
    ID="$(_id)"
    CMD=$(aws ssm send-command --region "$REGIAO" --instance-ids "$ID" \
      --document-name "AWS-RunShellScript" \
      --parameters 'commands=["journalctl -u medassist-api -n 40 --no-pager"]' \
      --query "Command.CommandId" --output text)
    aws ssm wait command-executed --command-id "$CMD" --instance-id "$ID" --region "$REGIAO" 2>/dev/null
    aws ssm get-command-invocation --command-id "$CMD" --instance-id "$ID" --region "$REGIAO" \
      --query "StandardOutputContent" --output text
    ;;

  acesso)
    shift
    [ $# -gt 0 ] || { echo "Informe ao menos um CIDR. Ex.: ./medassist.sh acesso 189.1.2.3/32" >&2; exit 1; }
    LISTA=$(printf '"%s",' "$@"); LISTA="[${LISTA%,}]"
    terraform -chdir="$DIR" apply -auto-approve -var="ips_liberados=$LISTA"
    ;;

  publico)
    terraform -chdir="$DIR" apply -auto-approve -var='ips_liberados=["0.0.0.0/0"]'
    ;;

  *)
    sed -n '2,16p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 1
    ;;
esac
