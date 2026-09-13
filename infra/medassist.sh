#!/usr/bin/env bash
# Controle da máquina do MedAssistPro na AWS.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export AWS_PROFILE="${AWS_PROFILE:-selvs}"
REGIAO="${AWS_REGION:-us-east-1}"

ajuda() {
  cat <<'AJUDA'
MedAssistPro — controle da máquina na AWS

  ./medassist.sh [opções]

MÁQUINA
  --status          estado atual, endereço e IP fixo
  --ligar           liga a máquina e espera ficar pronta
  --desligar        desliga (preserva disco e IP, para a cobrança por hora)
  --conectar        abre um terminal dentro da máquina (Session Manager)
  --logs            últimas linhas do serviço da API

INSTALAÇÃO
  --preparar        instala e configura tudo na máquina: pacotes, Node, Caddy,
                    código do projeto, arquivos do Git LFS, ambiente Python,
                    interface compilada, serviço da API e download do modelo.
                    É o passo obrigatório depois de criar a máquina, e pode ser
                    repetido sem quebrar nada. (~10 min)
  --indexar-rag     constrói o índice do RAG com 10 mil bulas (+10 min)
  --treinar         gera o dataset interno, anonimiza, treina o adapter e passa
                    a usar o modelo novo (+5 min)

MODO DO SITE (muda o comportamento do site publicado)
  --ativar-mock     respostas sintéticas, sem carregar o modelo. Rápido, serve
                    para demonstrar o fluxo sem GPU.
  --ativar-gpu      respostas do modelo real, na GPU. Primeira chamada leva
                    cerca de 2 minutos, porque o modelo é carregado.

ACESSO AO SITE
  --publico         libera o site para a internet
  --acesso CIDR     restringe o site a um ou mais IPs, ex.: --acesso 189.1.2.3/32

EXEMPLOS
  ./medassist.sh --status
  ./medassist.sh --preparar --indexar-rag --treinar     # máquina nova, completa
  ./medassist.sh --ativar-mock                          # site sem GPU
  ./medassist.sh --ativar-gpu                           # site com o modelo real
  ./medassist.sh --desligar

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

# Troca o modo do serviço da API (mock ou GPU) e reinicia.
_modo() {
  local mock="$1" descricao="$2"
  _remoto "$descricao" "[\"sed -i 's/^Environment=LLM_MOCK=.*/Environment=LLM_MOCK=$mock/' /etc/systemd/system/medassist-api.service\",\"systemctl daemon-reload\",\"systemctl restart medassist-api\",\"grep Environment /etc/systemd/system/medassist-api.service\"]"
}

[ $# -eq 0 ] && { ajuda; exit 0; }

PREPARAR=0
OPCOES_PREPARO=""
ACOES=()
IPS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --help|-h)      ajuda; exit 0 ;;
    --status|--ligar|--desligar|--conectar|--logs|--publico|--ativar-mock|--ativar-gpu) ACOES+=("$1") ;;
    --preparar)     PREPARAR=1 ;;
    --indexar-rag)  PREPARAR=1; OPCOES_PREPARO="$OPCOES_PREPARO --indexar-rag" ;;
    --treinar)      PREPARAR=1; OPCOES_PREPARO="$OPCOES_PREPARO --treinar" ;;
    --acesso)       shift; while [ $# -gt 0 ] && [[ "$1" != --* ]]; do IPS+=("$1"); shift; done; ACOES+=("--acesso"); continue ;;
    *) echo "opção desconhecida: $1" >&2; echo; ajuda; exit 1 ;;
  esac
  shift
done

# Se pediu mock junto da preparação, o modelo nem é baixado.
for a in ${ACOES[@]+"${ACOES[@]}"}; do
  [ "$a" = "--ativar-mock" ] && [ "$PREPARAR" = "1" ] && OPCOES_PREPARO="$OPCOES_PREPARO --mock"
done

if [ "$PREPARAR" = "1" ]; then
  B64=$(base64 -w0 "$DIR/preparar_maquina.sh")
  _remoto "Preparando a máquina$OPCOES_PREPARO. Pode levar de 10 a 30 minutos." \
    "[\"echo $B64 | base64 -d > /root/preparar_maquina.sh\",\"chmod +x /root/preparar_maquina.sh\",\"/root/preparar_maquina.sh$OPCOES_PREPARO\"]"
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
    --ativar-mock) _modo 1 "Trocando o site para modo mock..." ;;
    --ativar-gpu)  _modo 0 "Trocando o site para o modelo real na GPU..." ;;
    --publico)  terraform -chdir="$DIR" apply -auto-approve -var='ips_liberados=["0.0.0.0/0"]' ;;
    --acesso)
      [ ${#IPS[@]} -gt 0 ] || { echo "Informe ao menos um CIDR. Ex.: --acesso 189.1.2.3/32" >&2; exit 1; }
      LISTA=$(printf '"%s",' "${IPS[@]}"); LISTA="[${LISTA%,}]"
      terraform -chdir="$DIR" apply -auto-approve -var="ips_liberados=$LISTA"
      ;;
  esac
done
