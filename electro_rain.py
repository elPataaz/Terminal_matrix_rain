#!/usr/bin/env python3
"""
electro_rain.py — Terminal typewriter with morse beeps.
Runs after Pygame splash closes. Types the prompt, ready to go.
"""

import sys, os, time, random, math, signal, atexit, array

W = sys.stdout.write
def fl(): sys.stdout.flush()
def pos(r, c): return f'\033[{r+1};{c+1}H'
RST  = '\033[0m'
CLR  = '\033[2J\033[H'
HIDE = '\033[?25l'
SHOW = '\033[?25h'

def restore():
    W(SHOW + RST); fl()
atexit.register(restore)
signal.signal(signal.SIGINT, lambda *_: sys.exit(0))

try:
    ts = os.get_terminal_size()
    COLS, ROWS = ts.columns, ts.lines
except Exception:
    sys.exit(0)

# ── Beep sounds via pygame.mixer ─────────────────────────────
beep_available = False
try:
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
    import pygame.mixer as mx
    mx.init(frequency=44100, size=-16, channels=1, buffer=512)

    def make_beep(freq, dur_ms, vol=0.12):
        sr = 44100
        n = int(sr * dur_ms / 1000)
        buf = array.array('h', [0] * n)
        fade = int(sr * 0.003)
        for i in range(n):
            env = 1.0
            if i < fade: env = i / fade
            elif i > n - fade: env = (n - i) / fade
            buf[i] = max(-32767, min(32767, int(32767 * vol * env * math.sin(2 * math.pi * freq * i / sr))))
        return mx.Sound(buffer=buf)

    beep_hi = make_beep(1000, 35, 0.12)
    beep_lo = make_beep(600, 50, 0.10)
    beep_at = make_beep(1400, 60, 0.15)
    beep_available = True
except Exception:
    pass

def play_beep(ch):
    if not beep_available: return
    if ch == '@': beep_at.play()
    elif ch in '/:~%': beep_lo.play()
    else: beep_hi.play()

# ── Main ─────────────────────────────────────────────────────
def main():
    W(HIDE + CLR); fl()
    time.sleep(0.3)

    prompt = "edddie@MacBookAir:~/Dev/electrorecon % "
    user_host_end = 17
    colon_pos = 17
    path_start = 18
    path_end = 36

    tr = ROWS - 1
    tc = 0

    for i, ch in enumerate(prompt):
        if ch == ' ':
            W(f'{pos(tr, tc + i)} ')
            fl()
            time.sleep(0.06)
            continue

        if i < user_host_end:
            color = "255;60;60"
        elif i == colon_pos:
            color = "220;220;220"
        elif path_start <= i < path_end:
            color = "0;255;70"
        else:
            color = "220;220;220"

        play_beep(ch)
        W(f'{pos(tr, tc + i)}\033[38;2;{color}m{ch}')
        fl()
        time.sleep(0.10 + random.uniform(0, 0.07))

    time.sleep(0.5)
    W(SHOW + RST)
    W(f'\033[{ROWS};1H')
    fl()

    if beep_available:
        time.sleep(0.1)
        mx.quit()

main()
