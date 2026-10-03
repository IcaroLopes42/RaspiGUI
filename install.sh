#!/bin/bash
# install.sh - roda uma vez pra preparar o Pi
set -e

echo "== Habilitando interface SPI (necessária pra tela) =="
sudo raspi-config nonint do_spi 0

echo "== Instalando dependências de sistema =="
sudo apt update
sudo apt install -y python3-pip python3-venv libjpeg-dev zlib1g-dev \
    libfreetype6-dev network-manager

echo "== Criando ambiente virtual Python =="
python3 -m venv /home/kali/pi-dashboard/venv
source /home/kali/pi-dashboard/venv/bin/activate
pip install --upgrade pip
pip install -r /home/kali/pi-dashboard/requirements.txt

echo "== Habilitando autologin na tty1 =="
sudo raspi-config nonint do_boot_behaviour B2   # B2 = console autologin

echo "== Configurando disparo automático no login (só na tty1, não via SSH) =="
BASHRC_LINE='if [ "$(tty)" = "/dev/tty1" ]; then ~/pi-dashboard/boot.sh; fi'
if ! grep -qF "$BASHRC_LINE" ~/.bash_profile 2>/dev/null; then
    echo "$BASHRC_LINE" >> ~/.bash_profile
fi

echo ""
echo "Instalação concluída."
echo "IMPORTANTE antes de reiniciar, edite dashboard.py na seção CONFIG:"
echo "  - driver do chip da tela (linha do 'from luma.lcd.device import ...')"
echo "  - pinos GPIO_DC / GPIO_RST"
echo "  - usuário/senha SSH exibidos na tela"
echo ""
echo "Pra testar sem reiniciar: ./boot.sh"
echo "Pra reverter o autologin: sudo raspi-config  (System Options > Boot > Console)"
