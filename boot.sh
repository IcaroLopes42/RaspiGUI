#!/bin/bash
# boot.sh - dispara no autologin da tty1 (ver instruções em README.md)
# Ordem: checa/configura wifi -> abre o dashboard na tela LCD

cd "$(dirname "$0")"
source venv/bin/activate

python3 wifi_setup.py
STATUS=$?

if [ $STATUS -eq 0 ]; then
    exec python3 dashboard.py
else
    echo ""
    echo "Rede não configurada. Você está num shell normal (kali@raspberry)."
    echo "Rode 'python3 wifi_setup.py' manualmente quando quiser tentar de novo,"
    echo "ou 'python3 dashboard.py' pra abrir a tela mesmo sem rede."
fi
