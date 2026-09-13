#!/usr/bin/env bash
# Conferência estática do medassist.sh, para rodar antes de commitar.
#
# Pega o tipo de erro que já aconteceu aqui: função chamada mas não definida,
# opção documentada mas não tratada, e erro de sintaxe.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
falhas=0

echo "1. Sintaxe"
for f in "$DIR/medassist.sh" "$DIR/preparar_maquina.sh"; do
  if bash -n "$f"; then echo "   ok  $(basename "$f")"; else echo "   FALHA $(basename "$f")"; falhas=1; fi
done

echo "2. Funções chamadas mas não definidas"
if python3 - "$DIR/medassist.sh" <<'PY'
import re, sys
s = open(sys.argv[1], encoding="utf-8").read()
definidas = set(re.findall(r'^(_[a-z_]+)\(\) \{', s, re.M))
chamadas = set(re.findall(r'(?<![\w-])(_[a-z_]+)\b(?! *\(\))', s))
faltando = sorted(c for c in chamadas if c not in definidas)
print("   " + ("ok  nenhuma" if not faltando else "FALTA: " + ", ".join(faltando)))
sys.exit(1 if faltando else 0)
PY
then :; else falhas=1; fi

echo "3. Opções da ajuda tratadas no código"
for op in $(grep -oE '^  --[a-z-]+' "$DIR/medassist.sh" | tr -d ' ' | sort -u); do
  if grep -q -- "$op)" "$DIR/medassist.sh"; then echo "   ok  $op"; else echo "   FALTA $op"; falhas=1; fi
done

echo "4. Opções da esteira existentes no script"
for op in $(grep -oE '^          - [a-z-]+' "$DIR/../.github/workflows/medassist.yml" | awk '{print $2}'); do
  case "$op" in
    modelo|liberar-ip) echo "   ok  $op (tratada com valor)" ;;
    *) if grep -q -- "--$op)" "$DIR/medassist.sh"; then echo "   ok  $op"; else echo "   FALTA $op"; falhas=1; fi ;;
  esac
done

echo
if [ "$falhas" = "0" ]; then echo "Tudo certo."; else echo "Há falhas acima."; exit 1; fi
