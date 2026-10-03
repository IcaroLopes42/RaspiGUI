#!/usr/bin/env python3
"""
wifi_setup.py
Checa se o Raspberry Pi tem conexão de rede funcional.
Se não tiver, lista as redes wifi disponíveis, pede pro usuário escolher
e conecta. Feito pra rodar ANTES do dashboard.py, num terminal com teclado.

Requisitos: NetworkManager (nmcli) instalado e ativo.
Kali ARM recente já vem com NetworkManager por padrão. Se não tiver:
    sudo apt install network-manager
    sudo systemctl enable --now NetworkManager
"""

import subprocess
import socket
import sys
import time

CHECK_HOST = "1.1.1.1"
CHECK_PORT = 53
CHECK_TIMEOUT = 3


def tem_internet() -> bool:
    """Testa conectividade real (não só se tem um AP associado)."""
    try:
        socket.setdefaulttimeout(CHECK_TIMEOUT)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((CHECK_HOST, CHECK_PORT))
        return True
    except OSError:
        return False


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()


def listar_redes() -> list[dict]:
    """Retorna lista de redes: [{ssid, signal, security}], sem duplicatas, ordenada por sinal."""
    # força um rescan antes de listar
    subprocess.run(["nmcli", "dev", "wifi", "rescan"], capture_output=True)
    time.sleep(2)

    saida = run(["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi", "list"])
    redes = {}
    for linha in saida.splitlines():
        partes = linha.split(":")
        if len(partes) < 3:
            continue
        ssid, signal, security = partes[0], partes[1], partes[2]
        if not ssid:
            continue
        sinal_int = int(signal) if signal.isdigit() else 0
        # mantém só o de maior sinal quando o SSID se repete (múltiplos APs/mesh)
        if ssid not in redes or redes[ssid]["signal"] < sinal_int:
            redes[ssid] = {"ssid": ssid, "signal": sinal_int, "security": security or "--"}

    return sorted(redes.values(), key=lambda r: r["signal"], reverse=True)


def conectar(ssid: str, senha: str | None) -> bool:
    cmd = ["nmcli", "dev", "wifi", "connect", ssid]
    if senha:
        cmd += ["password", senha]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return True
    print(f"[ERRO] Falha ao conectar: {result.stderr.strip()}")
    return False


def fluxo_interativo():
    print("Sem conexão detectada. Escaneando redes...\n")
    redes = listar_redes()

    if not redes:
        print("Nenhuma rede encontrada. Verifique o adaptador wifi (rfkill list, ip link).")
        sys.exit(1)

    for i, r in enumerate(redes):
        cadeado = "🔒" if r["security"] != "--" else "  "
        print(f"[{i}] {cadeado} {r['ssid']:<30} sinal: {r['signal']}%")

    escolha = input("\nDigite o número da rede: ").strip()
    if not escolha.isdigit() or not (0 <= int(escolha) < len(redes)):
        print("Opção inválida.")
        sys.exit(1)

    rede = redes[int(escolha)]
    senha = None
    if rede["security"] != "--":
        import getpass
        senha = getpass.getpass(f"Senha para '{rede['ssid']}': ")

    print(f"\nConectando a '{rede['ssid']}'...")
    if conectar(rede["ssid"], senha):
        print("Conectado com sucesso!")
    else:
        print("Não foi possível conectar. Tente novamente.")
        sys.exit(1)


def main():
    if tem_internet():
        print("Conexão já ativa, prosseguindo.")
        sys.exit(0)

    tentativas = 0
    while not tem_internet() and tentativas < 3:
        fluxo_interativo()
        time.sleep(2)
        tentativas += 1

    if tem_internet():
        print("Rede configurada com sucesso.")
        sys.exit(0)
    else:
        print("Não foi possível estabelecer conexão após várias tentativas.")
        sys.exit(1)


if __name__ == "__main__":
    main()
