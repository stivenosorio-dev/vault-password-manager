# ── Constantes de configuración ───────────────────────────────────────────────

# Nombre del archivo donde se guardan los datos encriptados
VAULT_FILENAME = "vault.vault"

# Iteraciones PBKDF2 — cuántas veces se hashea la contraseña para derivar la clave.
# Más iteraciones = más seguro pero más lento al abrir. 480.000 es el estándar NIST 2023.
PBKDF2_ITERATIONS = 480_000

# Tamaño del salt en bytes (16 bytes = 128 bits — suficiente según NIST)
SALT_SIZE = 16

# Versión del formato del vault (para compatibilidad futura al modularizar)
VAULT_VERSION = "1.0"

import json
from pathlib import Path

# ── Paletas de colores de la UI (Temas) ───────────────────────────────────────
THEMES = {
    "Gold Obsidian": {
        "bg_dark": "#090909",
        "bg_panel": "#161716",
        "bg_input": "#0D0D0D",
        "bg_row": "#161716",
        "bg_row_alt": "#1C1D1C",
        "bg_row_sel": "#b87400",
        "accent": "#f6a700",
        "accent_hover": "#fed353",
        "accent_danger": "#712D52",
        "accent_ok": "#5AF7A0",
        "text_primary": "#FFFFFF",
        "text_secondary": "#B0B0B0",
        "text_dim": "#606060",
        "border": "#2A2A2A",
        "gold": "#fed353"
    },
    "Electric Azure": {
        "bg_dark": "#0A0C1A",
        "bg_panel": "#14182E",
        "bg_input": "#1C223D",
        "bg_row": "#14182E",
        "bg_row_alt": "#1A203B",
        "bg_row_sel": "#2d26e1",
        "accent": "#006ff2",
        "accent_hover": "#4e98f3",
        "accent_danger": "#FF4B4B",
        "accent_ok": "#84b6f4",
        "text_primary": "#F0F4FF",
        "text_secondary": "#84b6f4",
        "text_dim": "#4E5A85",
        "border": "#242C52",
        "gold": "#FED353"
    },
    "Nordic Heritage": {
        "bg_dark": "#ede6db",
        "bg_panel": "#F7F2EB",
        "bg_input": "#FFFFFF",
        "bg_row": "#F7F2EB",
        "bg_row_alt": "#F1EAE0",
        "bg_row_sel": "#8fbdd3",
        "accent": "#9d5353",
        "accent_hover": "#a2b38b",
        "accent_danger": "#9d5353",
        "accent_ok": "#789162",
        "text_primary": "#4A443F",
        "text_secondary": "#7D756D",
        "text_dim": "#AFA8A0",
        "border": "#e9d5da",
        "gold": "#ce8600"
    }
}

THEME_CONFIG_FILE = Path(__file__).parent / "theme.json"

def _load_theme() -> str:
    if THEME_CONFIG_FILE.exists():
        try:
            with open(THEME_CONFIG_FILE, "r") as f:
                data = json.load(f)
                t = data.get("theme", "Gold Obsidian")
                if t in THEMES:
                    return t
        except Exception:
            pass
    return "Gold Obsidian"

def set_active_theme(theme_name: str):
    global ACTIVE_THEME_NAME
    if theme_name in THEMES:
        ACTIVE_THEME_NAME = theme_name
        COLORS.update(THEMES[theme_name])
        try:
            with open(THEME_CONFIG_FILE, "w") as f:
                json.dump({"theme": theme_name}, f)
        except Exception:
            pass

ACTIVE_THEME_NAME = _load_theme()
COLORS = dict(THEMES[ACTIVE_THEME_NAME])# ── Fuentes ───────────────────────────────────────────────────────────────────
FONTS = {
    "title":    ("Segoe UI", 22, "bold"),
    "subtitle": ("Segoe UI", 12),
    "label":    ("Segoe UI", 10),
    "label_bold":("Segoe UI", 10, "bold"),
    "input":    ("Consolas", 11),      # Monoespaciada para contraseñas
    "button":   ("Segoe UI", 10, "bold"),
    "table":    ("Segoe UI", 10),
    "small":    ("Segoe UI", 9),
    "icon":     ("Segoe UI Emoji", 14),
}

