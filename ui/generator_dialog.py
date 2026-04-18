# ══════════════════════════════════════════════════════════════════════════════
# GeneratorMixin — Generador de contraseñas seguras
# ══════════════════════════════════════════════════════════════════════════════
# Responsabilidad: generar contraseñas criptográficamente seguras.
#   - _generar_password(): función pura, sin UI, reutilizable desde otros módulos
#   - _abrir_generador():  ventana independiente con slider de longitud
#
# Patrón: Mixin heredado por VaultApp.
# ══════════════════════════════════════════════════════════════════════════════
 
import secrets
import string
import tkinter as tk
from tkinter import ttk
 
from config.constants import COLORS, FONTS
 
 
class GeneratorMixin:

    def _generar_password(self, longitud: int = 20) -> str:
        """
        Genera una contraseña aleatoria criptográficamente segura.

        Usa secrets.choice() que garantiza aleatoriedad criptográfica
        (a diferencia de random.choice() que es predecible).

        Args:
            longitud: número de caracteres (default 20)

        Retorna:
            str: contraseña generada
        """
        # Alfabeto: mayúsculas + minúsculas + dígitos + símbolos seguros
        alfabeto = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"

        # Garantizar al menos un carácter de cada tipo
        pwd = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*()-_=+"),
        ]

        # Rellenar el resto con caracteres aleatorios del alfabeto completo
        pwd += [secrets.choice(alfabeto) for _ in range(longitud - 4)]

        # Mezclar para que los caracteres obligatorios no queden siempre al inicio
        secrets.SystemRandom().shuffle(pwd)

        return "".join(pwd)

    def _abrir_generador(self):
        """Abre una ventana independiente para generar y copiar contraseñas."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Generador de contraseñas")
        dlg.configure(bg=COLORS["bg_dark"])
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.geometry("440x320")
        self._centrar_ventana_hija(dlg, 440, 320)

        tk.Label(
            dlg, text="🔑 Generador de Contraseñas",
            font=FONTS["title"], bg=COLORS["bg_dark"], fg=COLORS["text_primary"]
        ).pack(pady=(20,16), padx=20, anchor="w")

        # Slider de longitud
        tk.Label(dlg, text="Longitud:", font=FONTS["label_bold"],
                 bg=COLORS["bg_dark"], fg=COLORS["text_secondary"]).pack(padx=20, anchor="w")

        var_long = tk.IntVar(value=20)
        frame_long = tk.Frame(dlg, bg=COLORS["bg_dark"])
        frame_long.pack(fill="x", padx=20)

        slider = ttk.Scale(frame_long, from_=8, to=40, orient="horizontal", variable=var_long)
        slider.pack(side="left", fill="x", expand=True)

        lbl_long = tk.Label(frame_long, textvariable=var_long, font=FONTS["label_bold"],
                            bg=COLORS["bg_dark"], fg=COLORS["accent"], width=3)
        lbl_long.pack(side="left", padx=8)

        # Campo de contraseña generada
        tk.Label(dlg, text="Contraseña generada:", font=FONTS["label_bold"],
                 bg=COLORS["bg_dark"], fg=COLORS["text_secondary"]).pack(padx=20, anchor="w", pady=(12,2))

        var_pwd = tk.StringVar()
        entry_gen = tk.Entry(dlg, textvariable=var_pwd, font=FONTS["input"],
                             bg=COLORS["bg_input"], fg=COLORS["accent"],
                             relief="flat", bd=6, state="readonly",
                             readonlybackground=COLORS["bg_input"])
        entry_gen.pack(fill="x", padx=20, ipady=8)

        def generar():
            var_pwd.set(self._generar_password(var_long.get()))

        def copiar():
            if var_pwd.get():
                dlg.clipboard_clear()
                dlg.clipboard_append(var_pwd.get())
                self._actualizar_estado("📋 Contraseña copiada al portapapeles")

        frame_btns = tk.Frame(dlg, bg=COLORS["bg_dark"])
        frame_btns.pack(fill="x", padx=20, pady=16)

        self._crear_boton(frame_btns, "⟳ Generar",  generar, color=COLORS["accent"]).pack(side="left", ipady=8)
        self._crear_boton(frame_btns, "📋 Copiar",   copiar,  color=COLORS["bg_input"]).pack(side="left", ipady=8, padx=8)
        self._crear_boton(frame_btns, "Cerrar", dlg.destroy,  color=COLORS["bg_input"]).pack(side="right", ipady=8)

        # Generar una contraseña al abrir
        generar()
