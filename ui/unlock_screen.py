# ══════════════════════════════════════════════════════════════════════════════
# Responsabilidad: todo lo relacionado con la pantalla inicial.
#   - Mostrar formulario de contraseña maestra
#   - Crear vault nuevo
#   - Verificar contraseña de vault existente
#   - Abrir vault desde ruta externa (Drive, USB)
#
# Patrón: Mixin — esta clase NO se instancia directamente.
# Es heredada por VaultApp (ui/app.py), que combina todos los mixins.
# Por eso usa 'self' libremente aunque aquí no haya __init__.
# ══════════════════════════════════════════════════════════════════════════════

import tkinter as tk
from tkinter import filedialog, messagebox
 
from config.constants import COLORS, FONTS
 
 
class UnlockMixin:
    
    def _mostrar_pantalla_desbloqueo(self):
        """
        Muestra la pantalla inicial de desbloqueo o creación de vault.
        Determina automáticamente si es primer uso o vault existente.
        """
        # Limpiar ventana
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.geometry("420x520")
        self._centrar_ventana(420, 520)
        self.root.resizable(False, False)

        # ── Frame principal centrado ──
        frame = tk.Frame(self.root, bg=COLORS["bg_dark"])
        frame.place(relx=0.5, rely=0.5, anchor="center")

        # Ícono candado
        tk.Label(
            frame, text="🔐", font=("Segoe UI Emoji", 52),
            bg=COLORS["bg_dark"], fg=COLORS["gold"]
        ).pack(pady=(0, 10))

        # Título
        tk.Label(
            frame, text="VAULT", font=("Segoe UI", 28, "bold"),
            bg=COLORS["bg_dark"], fg=COLORS["text_primary"]
        ).pack()

        # Subtítulo dinámico según si existe vault
        es_nuevo = not self.storage.existe()
        subtitulo = "Crea tu bóveda segura" if es_nuevo else "Ingresa tu contraseña maestra"
        tk.Label(
            frame, text=subtitulo, font=FONTS["subtitle"],
            bg=COLORS["bg_dark"], fg=COLORS["text_secondary"]
        ).pack(pady=(4, 30))

        # ── Campo de contraseña maestra ──
        tk.Label(
            frame, text="Contraseña maestra",
            font=FONTS["label_bold"], bg=COLORS["bg_dark"], fg=COLORS["text_secondary"]
        ).pack(anchor="w")

        self.entry_master = tk.Entry(
            frame, show="●", font=FONTS["input"], width=28,
            bg=COLORS["bg_input"], fg=COLORS["text_primary"],
            insertbackground=COLORS["accent"],
            relief="flat", bd=8
        )
        self.entry_master.pack(ipady=8, pady=(4, 12))
        self.entry_master.focus()

        # Campo de confirmación (solo en creación de vault nuevo)
        self.entry_confirm = None
        if es_nuevo:
            tk.Label(
                frame, text="Confirmar contraseña",
                font=FONTS["label_bold"], bg=COLORS["bg_dark"], fg=COLORS["text_secondary"]
            ).pack(anchor="w")

            self.entry_confirm = tk.Entry(
                frame, show="●", font=FONTS["input"], width=28,
                bg=COLORS["bg_input"], fg=COLORS["text_primary"],
                insertbackground=COLORS["accent"],
                relief="flat", bd=8
            )
            self.entry_confirm.pack(ipady=8, pady=(4, 12))

        # Mostrar/ocultar contraseña
        self.var_mostrar = tk.BooleanVar(value=False)
        tk.Checkbutton(
            frame, text="Mostrar contraseña", variable=self.var_mostrar,
            command=self._toggle_mostrar_password,
            bg=COLORS["bg_dark"], fg=COLORS["text_secondary"],
            selectcolor=COLORS["bg_input"], activebackground=COLORS["bg_dark"],
            font=FONTS["small"]
        ).pack(anchor="w", pady=(0, 20))

        # Botón principal
        texto_btn = "Crear Vault" if es_nuevo else "Desbloquear"
        btn = self._crear_boton(
            frame, texto_btn,
            lambda: self._accion_desbloqueo(es_nuevo),
            color=COLORS["accent"], ancho=28
        )
        btn.pack(ipady=10, pady=(0, 12))

        # Botón de abrir vault desde otra ubicación (Drive, USB, etc.)
        self._crear_boton_texto(
            frame, "📂  Abrir vault desde otra ubicación",
            self._abrir_vault_externo
        ).pack()

        # Bind Enter
        self.root.bind("<Return>", lambda e: self._accion_desbloqueo(es_nuevo))

        # Aviso de seguridad
        tk.Label(
            frame,
            text="⚠ Sin la contraseña maestra no hay recuperación posible.",
            font=FONTS["small"], bg=COLORS["bg_dark"], fg=COLORS["text_dim"],
            wraplength=300, justify="center"
        ).pack(pady=(20, 0))

    def _accion_desbloqueo(self, es_nuevo: bool):
        """
        Maneja el click en 'Crear Vault' o 'Desbloquear'.

        Args:
            es_nuevo: True si es creación de vault, False si es desbloqueo
        """
        pwd = self.entry_master.get().strip()

        if not pwd:
            messagebox.showwarning("Campo vacío", "Ingresa tu contraseña maestra.")
            return

        if len(pwd) < 6:
            messagebox.showwarning("Contraseña débil", "La contraseña debe tener al menos 6 caracteres.")
            return

        if es_nuevo:
            # Verificar que las contraseñas coincidan
            confirmar = self.entry_confirm.get().strip() if self.entry_confirm else ""
            if pwd != confirmar:
                messagebox.showerror("Error", "Las contraseñas no coinciden.")
                return

            # Crear vault nuevo
            self.clave = self.storage.crear_vault(pwd)
            self.password = pwd
            self.entradas = []
            self._mostrar_pantalla_principal()

        else:
            # Verificar contraseña existente
            # La derivación de PBKDF2 tarda ~1-2 segundos intencionalmente
            self.root.config(cursor="watch")
            self.root.update()

            ok, clave = self.storage.verificar_password(pwd)

            self.root.config(cursor="")

            if ok:
                self.clave = clave
                self.password = pwd
                self.entradas = self.storage.cargar_entradas(clave)
                self._mostrar_pantalla_principal()
            else:
                messagebox.showerror("Contraseña incorrecta", "La contraseña maestra no es válida.")

    def _toggle_mostrar_password(self):
        """Alterna entre mostrar y ocultar los campos de contraseña."""
        char = "" if self.var_mostrar.get() else "●"
        self.entry_master.config(show=char)
        if self.entry_confirm:
            self.entry_confirm.config(show=char)

    def _abrir_vault_externo(self):
        """Permite al usuario seleccionar un archivo .vault desde Drive u otra ubicación."""
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo vault",
            filetypes=[("Vault files", "*.vault"), ("All files", "*.*")]
        )
        if ruta:
            self.storage.cambiar_ruta(ruta)
            self._mostrar_pantalla_desbloqueo()
