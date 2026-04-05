#!/usr/bin/env python3
"""
electro_splash.py — Pygame Death Star matrix rain.
Ported from the HTML canvas reference. Terminal-sized window.
Tetris-style column fill, curved trench, oval dish, motion blur trails.
"""

import sys, os, random, math, array, subprocess

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame
from pygame import mixer

# ── Characters ──────────────────────────────────────────────
CHARS = 'ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789@#$%&*'
rc = lambda: CHARS[int(random.random() * len(CHARS))]

FPS = 40
FONT_SIZE = 14

# ── Terminal bounds ──────────────────────────────────────────
def get_terminal_bounds():
    script = '''
    tell application "Terminal"
        set b to bounds of front window
        return (item 1 of b) & "," & (item 2 of b) & "," & (item 3 of b) & "," & (item 4 of b)
    end tell
    '''
    try:
        out = subprocess.check_output(['osascript', '-e', script],
                                       text=True, stderr=subprocess.DEVNULL).strip()
        nums = [int(s.strip()) for s in out.replace(' ', '').split(',') if s.strip().lstrip('-').isdigit()]
        if len(nums) == 4:
            x, y, x2, y2 = nums
            return x, y, x2 - x, y2 - y
    except Exception:
        pass
    return None

# ── Imperial March ───────────────────────────────────────────
def make_tone(freq, duration_ms, volume=0.2):
    sr = 44100
    n = int(sr * duration_ms / 1000)
    buf = array.array('h', [0] * n)
    fade = int(sr * 0.008)
    for i in range(n):
        env = 1.0
        if i < fade: env = i / fade
        elif i > n - fade: env = (n - i) / fade
        buf[i] = max(-32767, min(32767, int(32767 * volume * env * math.sin(2 * math.pi * freq * i / sr))))
    return mixer.Sound(buffer=buf)

# ── Main ─────────────────────────────────────────────────────
def main():
    pygame.init()
    mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

    # Imperial March notes
    G4, Eb4, Bb4 = 392.0, 311.1, 466.2
    march_notes = [
        (G4, 400, 100), (G4, 400, 100), (G4, 400, 100),
        (Eb4, 280, 50), (Bb4, 120, 50),
        (G4, 400, 100),
        (Eb4, 280, 50), (Bb4, 120, 50),
        (G4, 600, 0),
    ]
    march_sounds = [(make_tone(f, d, 0.18), d + p) for f, d, p in march_notes]
    march_idx = 0
    march_timer = 0
    march_started = False

    # ── Window ───────────────────────────────────────────
    bounds = get_terminal_bounds()
    if bounds:
        wx, wy, SW, SH = bounds
        # Offset for title bar (~28px) and slight padding
        TITLE_BAR = 28
        PAD = 2
        wx += PAD
        wy += TITLE_BAR
        SW -= PAD * 2
        SH -= TITLE_BAR + PAD
        os.environ['SDL_VIDEO_WINDOW_POS'] = f'{wx},{wy}'
    else:
        try:
            ts = os.get_terminal_size()
            cols, rows = ts.columns, ts.lines
        except Exception:
            cols, rows = 80, 24
        SW, SH = int(cols * 10.8), int(rows * 21.0)
        info = pygame.display.Info()
        os.environ['SDL_VIDEO_WINDOW_POS'] = f'{(info.current_w-SW)//2},{(info.current_h-SH)//2}'

    screen = pygame.display.set_mode((SW, SH), pygame.NOFRAME)
    pygame.display.set_caption("ELECTRORECON")
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()

    # Motion blur overlay
    blur_surf = pygame.Surface((SW, SH), pygame.SRCALPHA)
    blur_surf.fill((0, 0, 0, 13))  # ~0.05 alpha like the HTML version

    # ── Font ─────────────────────────────────────────────
    font_path = "/Library/Fonts/Arial Unicode.ttf"
    if os.path.exists(font_path):
        font = pygame.font.Font(font_path, FONT_SIZE)
    else:
        font = pygame.font.SysFont("menlo", FONT_SIZE)
    FS = FONT_SIZE
    COLS = SW // FS
    ROWS = SH // FS

    # ── Death Star geometry ────────────────────────────────
    CX = COLS * 0.5
    CY = ROWS * 0.5
    R  = min(COLS, ROWS) * 0.40

    # Equatorial trench — FRONT ARC ONLY, with curve
    # Curved arc that dips down slightly at center (like your drawing)
    # Uses a gentle parabolic curve so it's not a flat line
    TRENCH_THICK = R * 0.04  # ~1-2 chars thick

    def in_trench(c, r):
        dx, dy = c - CX, r - CY
        d2 = dx*dx + dy*dy
        if d2 > R*R: return False
        # Front face only
        z2 = R*R - d2
        if z2 <= 0: return False
        z = math.sqrt(z2)
        if z < R * 0.3: return False
        # Curved center-line: slight downward arc at center
        # The trench follows y = 0.15*R * (1 - (dx/R)^2) — a gentle parabola
        curve_y = 0.15 * R * (1.0 - (dx / R) ** 2)
        dist_from_curve = abs(dy - curve_y)
        return dist_from_curve < TRENCH_THICK

    # Superlaser dish — upper-left, BIG, just black void
    DCX = CX - R * 0.34
    DCY = CY - R * 0.36
    DISH_RX = R * 0.24
    DISH_RY = R * 0.22

    def dish_val(c, r):
        ex, ey = c - DCX, r - DCY
        return (ex/DISH_RX)**2 + (ey/DISH_RY)**2

    def in_shape(c, r):
        dx, dy = c - CX, r - CY
        if dx*dx + dy*dy > R*R: return False
        if in_trench(c, r): return False
        if dish_val(c, r) <= 1: return False
        return True

    # 3D shade factor: cells near the limb (edge) are duller
    def shade_factor(c, r):
        """0.0 = limb (dark), 1.0 = center (bright). Simulates 3D lighting."""
        dx, dy = c - CX, r - CY
        d2 = dx*dx + dy*dy
        if d2 >= R*R: return 0.0
        # z-depth normalized: 1 at center, 0 at limb
        return math.sqrt(max(0, 1.0 - d2 / (R*R)))

    # Per-column valid rows (bottom → top)
    col_rows = [[] for _ in range(COLS)]
    mask_grid = [[in_shape(c, r) for c in range(COLS)] for r in range(ROWS)]
    trench_grid = [[in_trench(c, r) for c in range(COLS)] for r in range(ROWS)]

    for c in range(COLS):
        for r in range(ROWS - 1, -1, -1):
            if mask_grid[r][c]:
                col_rows[c].append(r)

    # Precompute shade for all cells inside sphere
    shade_grid = [[shade_factor(c, r) for c in range(COLS)] for r in range(ROWS)]

    # Edge cells: sphere rim, trench walls, dish ring
    edge_cells = []
    for r in range(1, ROWS - 1):
        for c in range(1, COLS - 1):
            dx, dy = c - CX, r - CY
            d2 = dx*dx + dy*dy

            # Sphere rim
            if mask_grid[r][c]:
                if not (mask_grid[r-1][c] and mask_grid[r+1][c] and
                        mask_grid[r][c-1] and mask_grid[r][c+1]):
                    edge_cells.append({'c': c, 'r': r, 'ch': rc(), 'type': 'outer'})
                    continue

            # Trench walls
            if trench_grid[r][c] and d2 <= R*R:
                adj = ((r > 0 and mask_grid[r-1][c]) or
                       (r < ROWS-1 and mask_grid[r+1][c]) or
                       (c > 0 and mask_grid[r][c-1]) or
                       (c < COLS-1 and mask_grid[r][c+1]))
                if adj:
                    edge_cells.append({'c': c, 'r': r, 'ch': rc(), 'type': 'trench'})
                    continue

            # Dish rim — just the outer edge, thin border
            dv = dish_val(c, r)
            if d2 <= R*R and not in_trench(c, r) and 0.7 <= dv <= 1.3:
                edge_cells.append({'c': c, 'r': r, 'ch': rc(), 'type': 'dish'})

    # ── Rain state ───────────────────────────────────────
    stacks = [[] for _ in range(COLS)]
    drops  = [[] for _ in range(COLS)]

    RAIN, FILL, DRAIN, HOLD, FADE = -1, 0, 1, 2, 3
    phase = RAIN
    phase_wait = 0
    HOLD_FRAMES = 120   # ~3 sec clean Death Star

    def spawn_drop(c):
        length = 5 + int(random.random() * 22)
        drops[c].append({
            'y': -(random.random() * ROWS * 0.6),
            'speed': 0.12 + random.random() * 0.45,
            'chars': [rc() for _ in range(length)],
            'bright': random.random() > 0.85,
        })

    # Spawn initial drops
    for c in range(COLS):
        if random.random() < 0.28:
            spawn_drop(c)

    # ── Music: MP3 if available, else generated tones ────
    mp3_path = os.path.expanduser("~/.config/matrix/march.mp3")
    use_mp3 = os.path.exists(mp3_path)
    if use_mp3:
        mixer.music.load(mp3_path)
        mixer.music.play(-1)  # loop
    march_started = not use_mp3  # only use generated tones if no mp3

    # ── Render cache ─────────────────────────────────────
    surf_cache = {}
    def get_surf(ch, color):
        key = (ch, color)
        if key not in surf_cache:
            surf_cache[key] = font.render(ch, True, color)
        return surf_cache[key]

    # ── State ────────────────────────────────────────────
    frame = 0
    fade_alpha = 0

    # ── Main loop ────────────────────────────────────────
    running = True
    while running:
        clock.tick(FPS)
        frame += 1

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_ESCAPE, pygame.K_q):
                running = False

        # ── Motion blur (like rgba(0,0,0,0.05)) ─────────
        screen.blit(blur_surf, (0, 0))

        # ── Update ───────────────────────────────────────
        # Refresh edge chars
        if frame % 7 == 0 and edge_cells:
            e = edge_cells[int(random.random() * len(edge_cells))]
            e['ch'] = rc()

        # Spawn drops
        if phase <= FILL:
            for c in range(COLS):
                if random.random() < 0.035 and len(drops[c]) < 4:
                    spawn_drop(c)

        # Move drops
        first_landed = False
        for c in range(COLS):
            col = drops[c]
            to_remove = []
            for i, d in enumerate(col):
                d['y'] += d['speed']
                if random.random() < 0.08:
                    d['chars'][int(random.random() * len(d['chars']))] = rc()

                row = int(d['y'])

                # Check if a drop reached the bottom
                if row >= ROWS - 1:
                    first_landed = True

                rows = col_rows[c]

                # Only catch drops during FILL phase
                if phase == FILL and len(rows) > 0:
                    stack_size = len(stacks[c])
                    if stack_size < len(rows):
                        if row >= rows[stack_size]:
                            stacks[c].append(rc())
                            to_remove.append(i)
                            continue

                if row - len(d['chars']) > ROWS:
                    to_remove.append(i)

            for i in reversed(to_remove):
                col.pop(i)

        # Phase transitions
        if phase == RAIN:
            # Let rain fall freely for a bit after text is gone
            phase_wait += 1
            if first_landed and phase_wait > FPS * 2:
                phase = FILL

        if phase == FILL:
            full = all(len(col_rows[c]) == 0 or len(stacks[c]) >= len(col_rows[c])
                       for c in range(COLS))
            if full:
                phase = DRAIN  # stop rain, let trailing drops finish

        elif phase == DRAIN:
            # Check if all drops have fallen off screen
            any_drops = any(len(drops[c]) > 0 for c in range(COLS))
            if not any_drops:
                phase = HOLD
                phase_wait = 0

        elif phase == HOLD:
            # Clean Death Star on screen, music still playing
            phase_wait += 1
            if phase_wait >= HOLD_FRAMES:
                phase = FADE
                fade_alpha = 0
                if use_mp3:
                    mixer.music.fadeout(800)

        elif phase == FADE:
            fade_alpha = min(255, fade_alpha + 10)
            if fade_alpha >= 255:
                running = False

        # Stack flicker
        for c in range(COLS):
            s = stacks[c]
            if s and random.random() < 0.003:
                s[int(random.random() * len(s))] = rc()


        # ── Render ───────────────────────────────────────
        px = lambda c: c * FS
        py = lambda r: r * FS

        # 1. Death Star outline — revealed by fill, not before.
        #    An edge cell only shows if the fill has reached its row.
        #    We track the highest (topmost) filled row per column.
        if phase >= FILL:
            # Build a quick lookup: highest filled row per column
            top_filled = {}
            for c in range(COLS):
                n = len(stacks[c])
                if n > 0 and len(col_rows[c]) > 0:
                    # col_rows is bottom-to-top, so stacks[c][-1] maps to the topmost filled
                    top_filled[c] = col_rows[c][n - 1]

            for e in edge_cells:
                er, ec = e['r'], e['c']
                # Only show if fill has reached this row in this or nearby columns
                revealed = False
                for nc in range(max(0, ec - 2), min(COLS, ec + 3)):
                    if nc in top_filled and top_filled[nc] <= er:
                        revealed = True
                        break
                # After DRAIN (fill complete), show everything
                if phase >= DRAIN:
                    revealed = True
                if not revealed:
                    continue

                sh = shade_grid[er][ec]
                if e['type'] == 'outer':
                    g = int(40 + 62 * sh)
                elif e['type'] == 'trench':
                    g = int(30 + 52 * sh)
                else:  # dish
                    g = int(25 + 40 * sh)
                color = (0, g, max(2, g // 12))
                screen.blit(get_surf(e['ch'], color), (px(ec), py(er)))

        # 2. Settled chars (Tetris fill with gradient + 3D shade)
        for c in range(COLS):
            s = stacks[c]
            rows = col_rows[c]
            n = len(s)
            if not n:
                continue
            for i in range(n):
                r = rows[i]
                t = i / (n - 1) if n > 1 else 1.0
                sh = shade_grid[r][c]  # 3D shade

                if i == n - 1:
                    # Bright flash on freshly landed, still shaded
                    g = int((160 + 95 * sh))
                    color = (int(160 * sh), g, int(160 * sh))
                else:
                    # Gradient with 3D shade: limb cells are duller
                    base_g = int(90 + t * 155)
                    g = int(base_g * (0.35 + 0.65 * sh))
                    color = (0, g, max(2, g // 15))

                screen.blit(get_surf(s[i], color), (px(c), py(r)))

        # 3. Active falling drops
        for c in range(COLS):
            for d in drops[c]:
                hr = int(d['y'])
                chars = d['chars']
                length = len(chars)
                bright = d['bright']

                for t in range(length):
                    r = hr - t
                    if r < 0 or r >= ROWS:
                        continue

                    if t == 0:
                        color = (255, 255, 255) if bright else (204, 255, 204)
                    else:
                        a = 1.0 - t / length
                        g = int((220 if bright else 180) * a)
                        color = (0, g, 0)

                    screen.blit(get_surf(chars[t], color), (px(c), py(r)))

        # ── Imperial March (loops until fade) ────────────
        if march_started and phase < FADE:
            march_timer -= 1
            if march_timer <= 0:
                if march_idx >= len(march_sounds):
                    march_idx = 0
                snd, wait_ms = march_sounds[march_idx]
                snd.play()
                march_timer = int(wait_ms / (1000.0 / FPS))
                march_idx += 1

        # ── Fade overlay ─────────────────────────────────
        if phase == FADE:
            fade_surf = pygame.Surface((SW, SH))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(fade_alpha)
            screen.blit(fade_surf, (0, 0))

        pygame.display.flip()

    pygame.quit()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit()
    except Exception:
        pygame.quit()
        raise
