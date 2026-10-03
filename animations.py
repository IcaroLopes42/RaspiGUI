"""
animations.py
Personagem pixel art simples com animação de "respiração" + piscar de olhos.
Desenhado por código (sem precisar de arquivos de imagem), então é fácil
trocar cores, formato e comportamento mexendo só nas constantes e na função
draw_frame().

Se preferir usar sprites de verdade (ex: baixados ou desenhados no Aseprite),
troque draw_frame() por um loader de spritesheet com Pillow (Image.open +
crop por frame) - a interface pra fora (frame_count, get_frame) continua igual.
"""

import math
from PIL import Image, ImageDraw

# ---- customize aqui ----
BODY_COLOR = (0, 255, 140)      # verde-neon, estilo "hacker"
EYE_COLOR = (10, 10, 10)
BG_COLOR = (5, 5, 15)
PIXEL = 4                        # tamanho de cada "pixel" lógico, em pixels reais
GRID_W, GRID_H = 24, 16          # resolução lógica do personagem (baixa = estilo retro)
FRAME_COUNT = 24                 # frames num ciclo completo de animação
# -------------------------


def _pixel_grid_to_image(grid: list[list[int]]) -> Image.Image:
    """Converte uma matriz 0/1 em uma imagem PIL, com upscale por PIXEL."""
    w, h = len(grid[0]), len(grid)
    img = Image.new("RGB", (w * PIXEL, h * PIXEL), BG_COLOR)
    draw = ImageDraw.Draw(img)
    for y, row in enumerate(grid):
        for x, val in enumerate(row):
            if val:
                draw.rectangle(
                    [x * PIXEL, y * PIXEL, (x + 1) * PIXEL - 1, (y + 1) * PIXEL - 1],
                    fill=BODY_COLOR,
                )
    return img


def _blob_grid(t: float, blink: bool) -> list[list[int]]:
    """Gera um 'blob' redondo que pulsa de tamanho com o tempo (efeito respiração)."""
    grid = [[0] * GRID_W for _ in range(GRID_H)]
    cx, cy = GRID_W / 2, GRID_H / 2
    base_r = min(GRID_W, GRID_H) / 3
    pulse = math.sin(t * 2 * math.pi) * 1.2  # amplitude da respiração
    r = base_r + pulse

    for y in range(GRID_H):
        for x in range(GRID_W):
            dx, dy = x - cx, (y - cy) * 1.3  # achata um pouco (elipse)
            if dx * dx + dy * dy <= r * r:
                grid[y][x] = 1

    # "olhos": dois buracos escuros, exceto quando piscando (linha fina)
    eye_y = int(cy - 1)
    eye_positions = [int(cx - 4), int(cx + 3)]
    for ex in eye_positions:
        if blink:
            if 0 <= ex < GRID_W:
                grid[eye_y][ex] = 0
        else:
            for oy in range(eye_y, eye_y + 2):
                for ox in range(ex, ex + 2):
                    if 0 <= oy < GRID_H and 0 <= ox < GRID_W:
                        grid[oy][ox] = 0

    return grid


def get_frame(index: int) -> Image.Image:
    """index vai de 0 a FRAME_COUNT-1, em loop."""
    t = index / FRAME_COUNT
    # pisca rapidamente por 2 frames a cada ciclo
    blink = index in (0, 1)
    grid = _blob_grid(t, blink)
    return _pixel_grid_to_image(grid)


def frame_size() -> tuple[int, int]:
    return GRID_W * PIXEL, GRID_H * PIXEL
