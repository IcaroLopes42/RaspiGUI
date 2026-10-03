#!/usr/bin/env python3
"""
dashboard.py
Desenha na tela LCD SPI: animação pixel art + CPU% + RAM% + IP + status do SSH
(ativo/inativo, usuário, se tem sessão conectada).

>>> AJUSTE OBRIGATÓRIO <<<
A seção CONFIG abaixo depende do chip exato da sua tela. Rode:
    pip show luma.lcd
    # e olhe o datasheet/anúncio da sua case pra achar o driver certo
Chips comuns em cases de Pi: st7789, ili9341, st7735, hx8357.
Se a imagem sair com cores trocadas ou invertida, normalmente é
gpio_DC/gpio_RST errado ou rotate errado - ajuste e teste.

Instalação (ver requirements.txt / install.sh):
    sudo apt install python3-pip python3-pil libjpeg-dev zlib1g-dev
    pip install luma.lcd psutil pillow
"""

import subprocess
import time
import socket

import psutil
from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import spi
from luma.lcd.device import st7789  # <-- troque aqui se seu chip for outro (ili9341, st7735...)

import animations

# ==================== CONFIG (ajuste pro seu hardware) ====================
SPI_PORT = 0
SPI_DEVICE = 0
GPIO_DC = 24        # data/command pin
GPIO_RST = 25        # reset pin
ROTATE = 0            # 0,1,2,3 -> gire se a imagem estiver de lado/invertida
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 240

SSH_USER = "kali"                 # usuário exibido na tela
SSH_PASSWORD = "sua_senha_aqui"   # troque isso, ou deixe em branco pra nunca mostrar
SHOW_PASSWORD = False              # True = mostra em texto puro. False = mascarado (••••••)

CLOUDFLARED_SERVICE = "cloudflared"                    # nome do serviço systemd (padrão do `cloudflared service install`)
CLOUDFLARED_CONFIG = "/etc/cloudflared/config.yml"      # onde fica o nome/hostname do túnel

REFRESH_SECONDS = 0.15             # ~6-7 fps, suficiente pra animação suave numa tela pequena
# ============================================================================

font_small = ImageFont.load_default()


def get_device():
    serial = spi(port=SPI_PORT, device=SPI_DEVICE, gpio_DC=GPIO_DC, gpio_RST=GPIO_RST)
    return st7789(serial, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, rotate=ROTATE)


def get_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("1.1.1.1", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "sem IP"


def ssh_status() -> dict:
    """Retorna se o serviço ssh está ativo e se há sessões conectadas."""
    ativo = subprocess.run(
        ["systemctl", "is-active", "ssh"], capture_output=True, text=True
    ).stdout.strip()

    # sessões ssh conectadas agora (via `who`, filtra terminais pts com origem remota)
    who_out = subprocess.run(["who"], capture_output=True, text=True).stdout
    conectado = any("(" in linha for linha in who_out.splitlines())  # IP entre parênteses = remoto

    return {
        "servico": "active" if ativo == "active" else "inactive",
        "sessao": "connected" if conectado else "idle",
    }


def cloudflared_status() -> dict:
    """Retorna se o serviço cloudflared está ativo e o nome/hostname do túnel configurado."""
    ativo = subprocess.run(
        ["systemctl", "is-active", CLOUDFLARED_SERVICE], capture_output=True, text=True
    ).stdout.strip()

    tunnel_nome = "?"
    try:
        with open(CLOUDFLARED_CONFIG) as f:
            for linha in f:
                linha = linha.strip()
                # parse simples de YAML, sem precisar da lib pyyaml:
                # procura "tunnel: <id-ou-nome>" no config.yml gerado pelo cloudflared
                if linha.startswith("tunnel:"):
                    tunnel_nome = linha.split(":", 1)[1].strip()
                    break
    except FileNotFoundError:
        tunnel_nome = "sem config"

    # cloudflared não expõe "conectado" via systemctl; active = processo rodando
    # e tentando manter a conexão. Pra status real da conexão, dá pra checar
    # `cloudflared tunnel info <nome>` via API, mas isso exige autenticação
    # extra - active/inactive já cobre o caso de uso do dashboard.
    return {
        "servico": "active" if ativo == "active" else "inactive",
        "tunnel": tunnel_nome,
    }


def draw_dashboard(draw: ImageDraw.ImageDraw, frame_img: Image.Image, w: int, h: int):
    # animação centralizada na parte de cima
    fh = frame_img.size[1]
    frame_area_bottom = fh + 10

    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    ip = get_ip()
    ssh = ssh_status()
    cf = cloudflared_status()

    y = frame_area_bottom
    linhas = [
        f"CPU: {cpu:4.1f}%   RAM: {ram:4.1f}%",
        f"IP: {ip}",
        f"SSH servico: {ssh['servico']}",
        f"SSH sessao:  {ssh['sessao']}",
        f"user: {SSH_USER}",
        f"pass: {SSH_PASSWORD if SHOW_PASSWORD else '••••••••'}",
        f"CF tunnel: {cf['servico']}",
        f"  -> {cf['tunnel']}",
    ]
    for linha in linhas:
        draw.text((4, y), linha, fill=(0, 255, 140), font=font_small)
        y += 12


def main():
    device = get_device()
    w, h = device.width, device.height
    frame_idx = 0

    while True:
        canvas = Image.new("RGB", (w, h), (5, 5, 15))
        frame_img = animations.get_frame(frame_idx)
        canvas.paste(frame_img, ((w - frame_img.width) // 2, 4))

        draw = ImageDraw.Draw(canvas)
        draw_dashboard(draw, frame_img, w, h)

        device.display(canvas)

        frame_idx = (frame_idx + 1) % animations.FRAME_COUNT
        time.sleep(REFRESH_SECONDS)


if __name__ == "__main__":
    main()
