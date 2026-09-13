#!/usr/bin/env bash
# Controle da máquina do MedAssistPro na AWS.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Na sua máquina, usa o perfil do SSO. Na esteira, as credenciais já vêm no
# ambiente (OIDC), e forçar um perfil inexistente quebraria tudo.
if [ -z "${AWS_PROFILE:-}" ] && [ -z "${AWS_ACCESS_KEY_ID:-}" ]; then
  export AWS_PROFILE=selvs
fi
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
  --indexar-rag e --treinar exigem uma máquina já preparada e rodam
  isoladamente. Se ela não estiver preparada, falham em vez de instalar.

  --preparar        instala e configura tudo: pacotes, Node, Caddy, código do
                    projeto, arquivos do Git LFS, ambiente Python, interface,
                    serviço da API e modelo. Repetir não quebra nada (~10 min)
  --indexar-rag     constrói o índice do RAG com 10 mil bulas (~10 min)
  --treinar         gera o dataset interno, anonimiza, treina o adapter e passa
                    a usar o modelo novo (~5 min)

MODELO QUE O SITE USA
  A troca já deixa o modelo carregado e respondendo, então leva ~3 min. Depois
  dela, a primeira consulta sai direto.

  --modelo biomistral-medquad-lora
                    treinado só com MedQuAD, e publicado no HuggingFace por
                    michelleAnogueira. É o "antes"
  --modelo biomistral-medassist-lora
                    treinado nesta máquina, com MedQuAD mais os dados internos
                    do hospital. É o "depois"

                    Outro valor é aceito como está, seja um repositório do
                    HuggingFace ou um caminho dentro da máquina.

QUEM PODE ABRIR O SITE
  Regra única, sempre substituída. Não é tocada por --ligar nem --preparar.

  --liberar-publico libera para a internet inteira, apagando as regras de IP
  --liberar-ip [IP...]
                    libera só os endereços informados, apagando a regra pública
                    e as anteriores. Sem argumento, usa o IP de quem rodou o
                    comando. A máscara é opcional: 189.1.2.3 vira 189.1.2.3/32.
                    Ex.: --liberar-ip   ou   --liberar-ip 200.1.2.0/24

DIA A DIA
  ./medassist.sh --ligar          # máquina pronta e site no ar
  ./medassist.sh --status
  ./medassist.sh --desligar       # sempre, ao terminar

SEQUÊNCIA PARA GRAVAR O ANTES E O DEPOIS DO FINE-TUNING
  ./medassist.sh --ligar              # máquina pronta e site no ar
  ./medassist.sh --indexar-rag        # busca em bulas ativa, fora da gravação
  ./medassist.sh --modelo biomistral-medquad-lora   # estado anterior ao treino
  ... grave a consulta: é o ANTES
  ./medassist.sh --treinar            # 3 min de treino, e já deixa o modelo
                                      # novo carregado e aquecido
  ... repita a mesma consulta: é o DEPOIS
  Para regravar o ANTES, volte com --modelo biomistral-medquad-lora.

Ligada custa cerca de US$ 0,80 por hora. Desligada, só disco e IP.
Usa o seu login do SSO. Se expirar: aws sso login --profile selvs
AJUDA
}

NOME="${NOME:-medassist}"
DOMINIO="${DOMINIO:-medassist.ia4.dev}"

# A máquina e o grupo de segurança são achados pela etiqueta, sem depender do
# Terraform. Assim o mesmo script serve aqui e na esteira do GitHub.
_id() {
  local id
  id=$(aws ec2 describe-instances --region "$REGIAO" \
    --filters "Name=tag:Name,Values=$NOME-gpu" \
              "Name=instance-state-name,Values=pending,running,stopping,stopped" \
    --query "Reservations[0].Instances[0].InstanceId" --output text) || {
    echo "Falha ao consultar a AWS. Confira as credenciais." >&2
    exit 1
  }
  if [ -z "$id" ] || [ "$id" = "None" ]; then
    echo "Máquina '$NOME-gpu' não encontrada. Crie com: terraform -chdir=$DIR apply" >&2
    exit 1
  fi
  echo "$id"
}

_grupo() {
  aws ec2 describe-security-groups --region "$REGIAO" \
    --filters "Name=group-name,Values=$NOME-instancia" \
    --query "SecurityGroups[0].GroupId" --output text
}

_ip_publico() {
  aws ec2 describe-instances --instance-ids "$(_id)" --region "$REGIAO" \
    --query "Reservations[0].Instances[0].PublicIpAddress" --output text
}

_regras_atuais() {
  # Uma regra por porta, então o mesmo CIDR aparece duas vezes: mostra sem repetir.
  aws ec2 describe-security-group-rules --region "$REGIAO" \
    --filters "Name=group-id,Values=$(_grupo)" \
    --query "SecurityGroupRules[?!IsEgress].CidrIpv4" --output text \
    | tr '\t' '\n' | sort -u | paste -sd' '
}

_modelo_atual() {
  local id; id="$(_id)"
  local cmd
  cmd=$(aws ssm send-command --region "$REGIAO" --instance-ids "$id" \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=["grep -oP \"(?<=^Environment=LLM_MODEL=).*\" /etc/systemd/system/medassist-api.service 2>/dev/null || echo -"]' \
    --query "Command.CommandId" --output text 2>/dev/null) || { echo "-"; return; }
  aws ssm wait command-executed --command-id "$cmd" --instance-id "$id" --region "$REGIAO" 2>/dev/null || true
  aws ssm get-command-invocation --command-id "$cmd" --instance-id "$id" --region "$REGIAO" \
    --query "StandardOutputContent" --output text 2>/dev/null | tr -d '[:space:]' || echo "-"
}

# Roda comandos dentro da máquina, mostrando a saída enquanto ela acontece.
#
# O Session Manager só devolve a saída quando o comando termina, o que deixava
# uma preparação de 20 minutos em silêncio. Por isso o comando grava tudo num
# arquivo na máquina, e aqui lemos esse arquivo de tempos em tempos.
_remoto() {
  local descricao="$1" comandos="$2"
  local id; id="$(_id)"
  echo "$descricao"

  local arquivo="/var/log/medassist-$(date +%s).log"
  # Redireciona todo o resto da execução para o arquivo (mesmo shell remoto).
  local com_log="[\"exec > $arquivo 2>&1\",${comandos#[}"

  local cmd
  cmd=$(aws ssm send-command --region "$REGIAO" --instance-ids "$id" \
    --document-name "AWS-RunShellScript" --timeout-seconds 7200 \
    --parameters "commands=$com_log" --query "Command.CommandId" --output text)

  local linhas=0 estado="Pending" novas
  while : ; do
    novas=$(_ler_arquivo "$id" "$arquivo" "$((linhas + 1))")
    if [ -n "$novas" ]; then
      printf '%s\n' "$novas"
      linhas=$((linhas + $(printf '%s\n' "$novas" | wc -l)))
    fi

    estado=$(aws ssm get-command-invocation --command-id "$cmd" --instance-id "$id" \
      --region "$REGIAO" --query "Status" --output text 2>/dev/null || echo "Pending")
    case "$estado" in
      Pending|InProgress|Delayed) ;;
      *) break ;;
    esac
  done

  novas=$(_ler_arquivo "$id" "$arquivo" "$((linhas + 1))")
  [ -n "$novas" ] && printf '%s\n' "$novas"

  if [ "$estado" != "Success" ]; then
    echo "Comando terminou como: $estado" >&2
    return 1
  fi
}

# Lê um arquivo da máquina a partir de uma linha. Cada leitura é um comando
# curto, e a espera entre elas vem do próprio tempo de ida e volta (~5 s).
_ler_arquivo() {
  local id="$1" arquivo="$2" desde="$3"
  local cmd
  cmd=$(aws ssm send-command --region "$REGIAO" --instance-ids "$id" \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[\"tail -n +$desde $arquivo 2>/dev/null || true\"]" \
    --query "Command.CommandId" --output text 2>/dev/null) || return 0
  aws ssm wait command-executed --command-id "$cmd" --instance-id "$id" --region "$REGIAO" 2>/dev/null || true
  local saida
  saida=$(aws ssm get-command-invocation --command-id "$cmd" --instance-id "$id" \
    --region "$REGIAO" --query "StandardOutputContent" --output text 2>/dev/null || true)
  [ "$saida" = "None" ] && saida=""
  printf '%s' "$saida"
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
# isso é assunto do --liberar-ip e do --liberar-publico.
_preparar() {
  local opcoes="${1:-}"
  local b64; b64=$(base64 -w0 "$DIR/preparar_maquina.sh")
  _remoto "Preparando a máquina$opcoes. Pode levar de 10 a 30 minutos." \
    "[\"echo $b64 | base64 -d > /root/preparar_maquina.sh\",\"chmod +x /root/preparar_maquina.sh\",\"/root/preparar_maquina.sh$opcoes\"]"
}

# Troca o adapter que o serviço da API usa.
_trocar_modelo() {
  local ref="$1"
  # Troca, reinicia e aquece: a carga do modelo (~2 min) acontece aqui, e não
  # na primeira consulta de quem for usar ou gravar.
  _remoto "Apontando o site para: $ref (inclui o carregamento do modelo)" \
    "[\"sed -i 's|^Environment=LLM_MODEL=.*|Environment=LLM_MODEL=$ref|' /etc/systemd/system/medassist-api.service\",\"systemctl daemon-reload\",\"systemctl restart medassist-api\",\"grep LLM_MODEL /etc/systemd/system/medassist-api.service\",\"curl -s --retry 60 --retry-delay 5 --retry-all-errors --max-time 600 -o /dev/null http://127.0.0.1:8000/health && echo 'API respondendo'\",\"curl -s --max-time 900 -o /dev/null -X POST http://127.0.0.1:8000/api/consulta -H 'Content-Type: application/json' -d '{\\\"relato\\\":\\\"Paciente com febre e tosse ha tres dias, sem dispneia.\\\"}' && echo 'Modelo carregado e respondendo.'\"]"
}

# IP público de quem está rodando o comando.
_meu_ip() {
  curl -s --max-time 10 https://checkip.amazonaws.com | tr -d '[:space:]'
}

# Grava a regra de acesso e aplica. Sempre substitui a regra anterior:
# rodar de novo com outro valor apaga o que existia antes (idempotente).
# Regra única: apaga todas as entradas e recria com os CIDRs informados.
# Feito pela API da AWS (não pelo Terraform), para a esteira poder usar.
_regra_acesso() {
  local descricao="$1"; shift
  local sg; sg="$(_grupo)"
  echo "$descricao"

  local antigas
  antigas=$(aws ec2 describe-security-group-rules --region "$REGIAO" \
    --filters "Name=group-id,Values=$sg" \
    --query "SecurityGroupRules[?!IsEgress].SecurityGroupRuleId" --output text)
  if [ -n "$antigas" ] && [ "$antigas" != "None" ]; then
    echo "  removendo as regras anteriores..."
    aws ec2 revoke-security-group-ingress --region "$REGIAO" --group-id "$sg" \
      --security-group-rule-ids $antigas >/dev/null
  fi

  local cidr
  for cidr in "$@"; do
    # Aceita o endereço sem máscara: 189.1.2.3 vira 189.1.2.3/32.
    case "$cidr" in *[!0-9./]*) echo "Endereço inválido: $cidr" >&2; exit 1 ;; esac
    case "$cidr" in */*) : ;; *) cidr="$cidr/32" ;; esac
    echo "  liberando portas 80 e 443 para $cidr..."
    aws ec2 authorize-security-group-ingress --region "$REGIAO" --group-id "$sg" \
      --ip-permissions \
        "IpProtocol=tcp,FromPort=80,ToPort=80,IpRanges=[{CidrIp=$cidr,Description=HTTP}]" \
        "IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges=[{CidrIp=$cidr,Description=HTTPS}]" \
      >/dev/null
  done
  echo "regra atual: $(_regras_atuais)"
}

# Posição atual da máquina. Vai para a tela e, na esteira, para o resumo.
_status() {
  local id estado ip modelo regras
  id="$(_id)"
  estado=$(aws ec2 describe-instances --instance-ids "$id" --region "$REGIAO" \
    --query 'Reservations[0].Instances[0].State.Name' --output text)
  ip="$(_ip_publico)"
  regras="$(_regras_atuais)"
  [ -n "$regras" ] || regras="nenhum IP liberado"
  if [ "$estado" = "running" ]; then modelo="$(_modelo_atual)"; else modelo="(máquina desligada)"; fi

  printf '%-18s %s\n' \
    "instância:" "$id" \
    "estado:" "$estado" \
    "endereço:" "https://$DOMINIO" \
    "ip fixo:" "$ip" \
    "modelo em uso:" "$modelo" \
    "quem abre o site:" "$regras"

  # Na esteira do GitHub, a mesma posição vai para o resumo da execução.
  if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
    {
      echo "### Posição do ambiente"
      echo
      echo "| item | valor |"
      echo "|---|---|"
      echo "| instância | \`$id\` |"
      echo "| estado | **$estado** |"
      echo "| endereço | https://$DOMINIO |"
      echo "| ip fixo | $ip |"
      echo "| modelo em uso | \`$modelo\` |"
      echo "| quem abre o site | $regras |"
      echo
    } >> "$GITHUB_STEP_SUMMARY"
  fi
}

[ $# -eq 0 ] && { ajuda; exit 0; }

PREPARAR=0
EXTRAS=""
ACOES=()
IPS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --help|-h)      ajuda; exit 0 ;;
    --status|--ligar|--desligar|--conectar|--logs|--liberar-publico) ACOES+=("$1") ;;
    --preparar)     PREPARAR=1 ;;
    --modelo)
      case "${2:-}" in
        biomistral-medquad-lora)   MODELO_REF="michelleAnogueira/biomistral-medquad-lora" ;;
        biomistral-medassist-lora) MODELO_REF="/opt/medassist/biomistral-medassist-lora" ;;
        "") echo "Informe o modelo. Ex.: --modelo biomistral-medassist-lora" >&2; exit 1 ;;
        # Qualquer outro valor passa direto: repositório do HuggingFace ou caminho na máquina.
        *) MODELO_REF="$2" ;;
      esac
      ACOES+=("--modelo"); shift ;;
    --indexar-rag)  EXTRAS="$EXTRAS --indexar-rag" ;;
    --treinar)      EXTRAS="$EXTRAS --treinar" ;;
    --liberar-ip)   shift; while [ $# -gt 0 ] && [[ "$1" != --* ]]; do IPS+=("$1"); shift; done; ACOES+=("--liberar-ip"); continue ;;
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

EXECUTOU=0
for acao in ${ACOES[@]+"${ACOES[@]}"}; do
  EXECUTOU=1
  case "$acao" in
    --status) _status ;;
    --ligar)
      ID="$(_id)"; echo "Ligando $ID..."
      aws ec2 start-instances --instance-ids "$ID" --region "$REGIAO" >/dev/null
      echo "  aguardando a máquina iniciar..."
      aws ec2 wait instance-running --instance-ids "$ID" --region "$REGIAO"
      echo "  máquina iniciada. Aguardando as checagens da AWS (leva ~1 min)..."
      aws ec2 wait instance-status-ok --instance-ids "$ID" --region "$REGIAO"
      echo "  checagens concluídas."
      if [ "$PREPARAR" = "0" ]; then
        echo "  verificando se a máquina já foi preparada..."
      fi
      if [ "$PREPARAR" = "0" ] && ! _preparada; then
        echo "Máquina ainda não preparada. Preparando agora (10 a 30 min, com andamento abaixo)..."
        _preparar ""
      fi
      echo "Pronta: https://$DOMINIO"
      echo "⚠️  Lembre de desligar ao terminar: ./medassist.sh --desligar"
      ;;
    --desligar)
      ID="$(_id)"; echo "Desligando $ID..."
      aws ec2 stop-instances --instance-ids "$ID" --region "$REGIAO" >/dev/null
      echo "  aguardando a máquina parar..."
      aws ec2 wait instance-stopped --instance-ids "$ID" --region "$REGIAO"
      echo "Desligada. Para de cobrar por hora; disco e IP continuam."
      ;;
    --conectar) aws ssm start-session --target "$(_id)" --region "$REGIAO" ;;
    --logs)     _remoto "Logs da API:" '["journalctl -u medassist-api -n 40 --no-pager"]' ;;
    --modelo)   _trocar_modelo "$MODELO_REF" ;;
    --liberar-publico) _regra_acesso "Liberando o site para a internet inteira..." "0.0.0.0/0" ;;
    --liberar-ip)
      if [ ${#IPS[@]} -eq 0 ]; then
        MEU_IP=$(_meu_ip)
        [ -n "$MEU_IP" ] || { echo "Não consegui descobrir seu IP. Informe manualmente: --liberar-ip 189.1.2.3/32" >&2; exit 1; }
        IPS=("$MEU_IP/32")
        echo "IP detectado: $MEU_IP"
      fi
      _regra_acesso "Restringindo o site aos IPs informados..." "${IPS[@]}"
      ;;
  esac
done

# Toda execução termina mostrando a posição do ambiente.
if [ "$PREPARAR" = "1" ] || [ -n "$EXTRAS" ] || { [ "${EXECUTOU:-0}" = "1" ] && ! printf '%s\n' ${ACOES[@]+"${ACOES[@]}"} | grep -q '^--status$'; }; then
  echo
  _status
fi
