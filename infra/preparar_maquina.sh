#!/usr/bin/env bash
# Prepara a instância da AWS para rodar o MedAssistPro.
#
# Roda DENTRO da máquina, como root. Normalmente chamado por:
#     ./medassist.sh preparar [opções]
#
# É idempotente: pode ser rodado de novo sem quebrar nada.
#
# Opções:
#   --apenas         pula a instalação e roda só as etapas pedidas abaixo
#                    (exige uma máquina já preparada)
#   --indexar-rag    constrói o índice do RAG (10 mil bulas, ~10 min na GPU)
#   --treinar        treina o adapter com os dados internos (~3 min na GPU)
#   --modelo <ref>   adapter a usar (padrão: o publicado no HuggingFace)
#   --repo <url>     repositório a clonar
set -euo pipefail

REPO="${REPO:-https://github.com/Flamers-Team/MedAssistPro.git}"
RAIZ=/opt/medassist
APP="$RAIZ/app"
VENV="$RAIZ/venv"
PYTHON_BASE=/opt/pytorch/bin/python      # ambiente com PyTorch e CUDA da imagem Deep Learning
DOMINIO="${DOMINIO:-medassist.ia4.dev}"
MODELO="${MODELO:-michelleAnogueira/biomistral-medquad-lora}"
# Adapter treinado nesta máquina, com MedQuAD + dados internos do hospital.
ADAPTER_TREINADO="$RAIZ/biomistral-medassist-lora"
INDEXAR=0
TREINAR=0
APENAS=0
MOCK=0   # o modo mock existe no código (LLM_MOCK) para testes e uso sem GPU,
         # mas nesta máquina, que é só GPU, a API sobe sempre com o modelo real.

while [ $# -gt 0 ]; do
  case "$1" in
    --indexar-rag|--indexar) INDEXAR=1 ;;
    --apenas)  APENAS=1 ;;
    --treinar) TREINAR=1 ;;
    --modelo)  MODELO="$2"; shift ;;
    --repo)    REPO="$2"; shift ;;
    *) echo "opção desconhecida: $1" >&2; exit 1 ;;
  esac
  shift
done

etapa() { echo; echo "=== $* ==="; }

if [ "$APENAS" = "0" ]; then

etapa "1/8 Pacotes do sistema"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git git-lfs curl debian-keyring debian-archive-keyring apt-transport-https >/dev/null
if ! command -v node >/dev/null; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash - >/dev/null 2>&1
  apt-get install -y -qq nodejs >/dev/null
fi
if ! command -v caddy >/dev/null; then
  curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key \
    | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt \
    > /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -qq && apt-get install -y -qq caddy >/dev/null
fi
echo "node $(node --version) | caddy $(caddy version | head -1)"

etapa "2/8 Código do projeto"
mkdir -p "$RAIZ"
if [ -d "$APP/.git" ]; then
  # Sincronização forçada: a máquina é descartável, o que vale é o repositório.
  # Limpa só as pastas de código, preservando data/ (índice do RAG, modelos).
  su - ubuntu -c "cd $APP && git fetch --depth 1 origin main && git reset --hard FETCH_HEAD && git clean -fdq -- backend frontend infra notebooks scripts docs"
else
  su - ubuntu -c "git clone --depth 1 $REPO $APP"
fi
# O ChatBulário está no repositório via Git LFS e o clone raso não traz o conteúdo.
su - ubuntu -c "cd $APP && git lfs install --skip-repo && git lfs pull"
chown -R ubuntu:ubuntu "$RAIZ"

etapa "3/8 Ambiente Python"
# Reaproveita o PyTorch com CUDA que já vem na imagem, em vez de baixar de novo.
[ -d "$VENV" ] || su - ubuntu -c "$PYTHON_BASE -m venv --system-site-packages $VENV"
su - ubuntu -c "$VENV/bin/pip install -q --upgrade pip"
su - ubuntu -c "cd $APP/backend && $VENV/bin/pip install -q -r requirements.txt"
su - ubuntu -c "$VENV/bin/pip install -q datasets requests pandas"
su - ubuntu -c "$VENV/bin/python -c 'import torch; print(\"torch\", torch.__version__, \"| cuda:\", torch.cuda.is_available())'"

etapa "4/8 Interface"
# O endereço da API precisa entrar na compilação, senão o navegador tenta 127.0.0.1.
su - ubuntu -c "cd $APP/frontend && npm ci --no-audit --no-fund >/dev/null 2>&1 && VITE_API_URL=https://$DOMINIO npm run build >/dev/null"
echo "interface compilada em $APP/frontend/dist"

etapa "5/8 Caddy"
sed "s|medassist.ia4.dev|$DOMINIO|g" "$APP/infra/Caddyfile" > /etc/caddy/Caddyfile
systemctl reload caddy 2>/dev/null || systemctl restart caddy
echo "caddy servindo https://$DOMINIO"

# Se já existe um adapter treinado nesta máquina, ele tem preferência sobre o
# publicado — a não ser que o usuário tenha passado outro em --modelo.
if [ "$TREINAR" = "0" ] && [ "$MODELO" = "michelleAnogueira/biomistral-medquad-lora" ] \
   && [ -f "$ADAPTER_TREINADO/adapter_config.json" ]; then
  MODELO="$ADAPTER_TREINADO"
  echo "adapter treinado encontrado nesta máquina: usando $MODELO"
fi

etapa "6/8 Modelo"
su - ubuntu -c "$VENV/bin/hf download BioMistral/BioMistral-7B" >/dev/null
su - ubuntu -c "$VENV/bin/hf download $MODELO" >/dev/null 2>&1 || echo "aviso: '$MODELO' não é um repositório do HuggingFace (deve ser um caminho local)"
echo "modelo base e adapter em cache"

else
  etapa "Modo --apenas: instalação pulada"
  # Ainda assim sincroniza o código, para pegar dataset e scripts atualizados.
  su - ubuntu -c "cd $APP && git fetch --depth 1 origin main && git reset --hard FETCH_HEAD && git clean -fdq -- backend frontend infra notebooks scripts docs"
  [ -f "$ADAPTER_TREINADO/adapter_config.json" ] && [ "$TREINAR" = "0" ] && MODELO="$ADAPTER_TREINADO"
fi

etapa "7/8 RAG"
if [ "$INDEXAR" = "1" ]; then
  su - ubuntu -c "cd $APP/backend && $VENV/bin/python src/rag/build_index_chatbulario.py 10000" 2>&1 | tail -3
else
  if [ -d "$APP/data/processed/chroma_index" ]; then
    echo "índice já existe (use --indexar para refazer)"
  else
    echo "sem índice: a busca em bulas fica vazia. Rode de novo com --indexar"
  fi
fi

etapa "8/8 Treino e serviço"
if [ "$TREINAR" = "1" ]; then
  su - ubuntu -c "cd $APP/backend && $VENV/bin/python src/data/00_gerar_dados_internos.py"
  su - ubuntu -c "cd $APP/backend && INPUT_FILE=../data/raw/dados_internos_hospital.jsonl OUTPUT_FILE=../data/processed/dados_internos_anonimizado.jsonl $VENV/bin/python src/data/01_anonimizar.py" | tail -3
  su - ubuntu -c "cd $APP/backend && $VENV/bin/python src/data/05_treinar_adapter.py ../data/processed/dados_internos_anonimizado.jsonl $ADAPTER_TREINADO" 2>&1 | tail -3
  MODELO="$ADAPTER_TREINADO"
fi

cat > /etc/systemd/system/medassist-api.service <<UNIT
[Unit]
Description=API do MedAssistPro (FastAPI)
After=network.target

[Service]
User=ubuntu
WorkingDirectory=$APP/backend
Environment=LLM_MOCK=$MOCK
Environment=LLM_MODEL=$MODELO
Environment=PYTHONUNBUFFERED=1
ExecStart=$VENV/bin/python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now medassist-api >/dev/null 2>&1
systemctl restart medassist-api

# Aquecimento: espera o modelo carregar e dispara uma consulta, para que os
# ~2 minutos de carga aconteçam aqui, e não na primeira consulta de quem usar.
etapa "Aquecendo o modelo"
if curl -s --retry 60 --retry-delay 5 --retry-all-errors --max-time 600 \
     -o /dev/null http://127.0.0.1:8000/health; then
  echo "API respondendo. Disparando consulta de aquecimento..."
  curl -s --max-time 900 -o /dev/null -X POST http://127.0.0.1:8000/api/consulta \
    -H 'Content-Type: application/json' \
    -d '{"relato":"Paciente com febre e tosse ha tres dias, sem dispneia."}' \
    && echo "Modelo carregado e respondendo." \
    || echo "Aviso: a consulta de aquecimento falhou; o site sobe mesmo assim."
else
  echo "Aviso: a API não respondeu a tempo. Veja: ./medassist.sh --logs"
fi

echo
echo "=================================================="
echo "PRONTO"
echo "  endereço: https://$DOMINIO"
echo "  modelo:   $MODELO (mock=$MOCK)"
echo "  login:    medico / demo123"
echo "=================================================="
echo "O modelo já está carregado: a próxima consulta responde direto."
