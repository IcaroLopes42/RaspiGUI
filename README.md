# Pi Dashboard

Dashboard pro Raspberry Pi 3B com tela LCD SPI: checa/configura wifi no boot,
depois mostra animação pixel art + CPU/RAM/IP/status SSH.

## 1. Instalação

```bash
git clone https://github.com/IcaroLopes42/RaspiGUI.git
cd pi-dashboard
chmod +x install.sh boot.sh
./install.sh
```

O `install.sh` habilita SPI, instala dependências, ativa autologin na tty1 e
configura o `~/.bash_profile` pra disparar `boot.sh` automaticamente — **só**
na tty1 (login físico), nunca numa sessão SSH.

## 2. Configuração obrigatória (hardware-specific)

Abra `dashboard.py`, seção `CONFIG`:

| Variável | O que é |
|---|---|
| `from luma.lcd.device import st7789` | Troque `st7789` pelo chip real da sua tela (`ili9341`, `st7735`, `hx8357`...) |
| `GPIO_DC`, `GPIO_RST` | Pinos do datasheet/manual da case |
| `DISPLAY_WIDTH/HEIGHT` | Resolução da tela |
| `SSH_USER`, `SSH_PASSWORD` | Credenciais mostradas na tela |
| `SHOW_PASSWORD` | `False` = mascarado (recomendado se o Pi ficar visível no hackerspace) |
| `CLOUDFLARED_SERVICE` | nome do serviço systemd do túnel (`cloudflared` é o padrão do `cloudflared service install`) |
| `CLOUDFLARED_CONFIG` | caminho do `config.yml` do túnel, de onde o nome é lido |

Se a imagem sair invertida/cortada, ajuste `ROTATE` (0-3).

## 3. Testar sem reiniciar

```bash
./boot.sh
```

## 4. Customizar a animação (pixel art)

Tudo em `animations.py`. É um "blob" respirando + piscando, desenhado por
código (sem precisar de arquivo de imagem). Pra mexer:

- **Cores**: mude `BODY_COLOR`, `BG_COLOR` no topo do arquivo.
- **Formato**: a função `_blob_grid()` decide quais pixels acendem, baseado
  numa distância do centro (`dx*dx + dy*dy <= r*r` = círculo/elipse). Troque
  essa condição pra outro formato.
- **Resolução**: `GRID_W`, `GRID_H` (baixo = mais "retro"), `PIXEL` (tamanho
  de cada quadradinho na tela real).
- **Sprites de verdade**: se quiser desenhar num editor (Aseprite, Piskel) em
  vez de gerar por código, troque `get_frame()` pra carregar frames de um
  spritesheet PNG com `PIL.Image.open()` + crop. A interface (`get_frame(i)`
  retorna uma `PIL.Image`) continua igual, então `dashboard.py` não muda.

## 5. Logs / debug

Como roda direto na tty (não como serviço systemd), os erros aparecem na
própria tela do Pi se você conectar um monitor/teclado, ou rode `./boot.sh`
manualmente via SSH pra ver os prints (a parte de dashboard trava o terminal
porque fica em loop desenhando — use Ctrl+C pra sair).

## Estrutura

```
pi-dashboard/
├── wifi_setup.py     # checa conexão, lista redes, conecta
├── dashboard.py      # loop principal: stats + animação na tela SPI
├── animations.py      # pixel art, fácil de customizar
├── boot.sh            # orquestra os dois acima, chamado no autologin
├── install.sh         # setup inicial (SPI, deps, autologin)
└── requirements.txt
```
