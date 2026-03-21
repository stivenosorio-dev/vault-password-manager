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

# ── Paleta de colores de la UI ────────────────────────────────────────────────
# Centralizada aquí para futura extracción a un módulo de tema (theme.py)

COLORS = {
    "bg_dark":      "#0F1117",   # Fondo principal — casi negro azulado
    "bg_panel":     "#1A1D2E",   # Fondo de paneles y tarjetas
    "bg_input":     "#252836",   # Fondo de campos de entrada
    "bg_row":       "#1E2130",   # Fondo de filas de la tabla
    "bg_row_alt":   "#242638",   # Fondo de filas alternas
    "bg_row_sel":   "#2D3561",   # Fondo de fila seleccionada
    "accent":       "#7C6AF7",   # Color principal — violeta
    "accent_hover": "#9B8DFF",   # Accent al pasar el mouse
    "accent_danger":"#F75A5A",   # Rojo para acciones peligrosas (eliminar)
    "accent_ok":    "#5AF7A0",   # Verde para acciones positivas
    "text_primary": "#E8E8F0",   # Texto principal
    "text_secondary":"#8888AA",  # Texto secundario / etiquetas
    "text_dim":     "#555570",   # Texto muy tenue
    "border":       "#2E3050",   # Color de bordes
    "gold":         "#F7C05A",   # Amarillo/dorado para el candado
}

# ── Fuentes ───────────────────────────────────────────────────────────────────
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

