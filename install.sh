#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  install.sh — Death Star Matrix Rain Terminal Splash
#
#  Run once:   bash install.sh
#  Then open a new terminal window to see the animation.
#  Requires: python3, pygame (pip3 install pygame)
# ─────────────────────────────────────────────────────────────

set -e

INSTALL_DIR="$HOME/.config/matrix"
ZSHRC="$HOME/.zshrc"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── 1. Install scripts ──────────────────────────────────────
mkdir -p "$INSTALL_DIR"
cp "$SRC_DIR/electro_splash.py" "$INSTALL_DIR/"
cp "$SRC_DIR/electro_rain.py" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/electro_splash.py" "$INSTALL_DIR/electro_rain.py"
echo "✓  Installed scripts → $INSTALL_DIR"

# ── 2. Check pygame ─────────────────────────────────────────
if python3 -c "import pygame" 2>/dev/null; then
    echo "✓  pygame found"
else
    echo "⚠  pygame not found. Installing..."
    pip3 install pygame
fi

# ── 3. Suppress Last Login message ──────────────────────────
touch "$HOME/.hushlogin"

# ── 4. Back up .zshrc ───────────────────────────────────────
if [ -f "$ZSHRC" ]; then
    cp "$ZSHRC" "$ZSHRC.bak_matrix"
    echo "✓  Backed up $ZSHRC → $ZSHRC.bak_matrix"
else
    touch "$ZSHRC"
fi

# ── 5. Add launch hook ──────────────────────────────────────
if grep -q "electro_splash" "$ZSHRC" 2>/dev/null; then
    echo "⚠  Already installed in $ZSHRC — skipping."
else
    cat >> "$ZSHRC" << 'BLOCK'

# ── Death Star Splash ────────────────────────────────────────
if [[ -o interactive && -z "$MATRIX_PLAYED" ]]; then
    export MATRIX_PLAYED=1
    python3 "$HOME/.config/matrix/electro_splash.py"
    python3 "$HOME/.config/matrix/electro_rain.py"
fi
BLOCK
    echo "✓  Added launch hook to $ZSHRC"
fi

# ── 6. Optional: MP3 ────────────────────────────────────────
if [ -f "$INSTALL_DIR/march.mp3" ]; then
    echo "✓  Music file found: $INSTALL_DIR/march.mp3"
else
    echo "   Optional: place an MP3 at $INSTALL_DIR/march.mp3 for music"
fi

echo ""
echo "  All done. Open a new terminal window to see the Death Star."
echo "  To uninstall: remove the hook from $ZSHRC and delete $INSTALL_DIR"
