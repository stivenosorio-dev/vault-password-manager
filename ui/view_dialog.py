# ══════════════════════════════════════════════════════════════════════════════
# ViewDialogMixin — Diálogo de visualización de una entrada
# ══════════════════════════════════════════════════════════════════════════════
# Responsabilidad: mostrar los detalles completos de una entrada del vault.
#   - Contraseña oculta por defecto con botón ojo para revelar
#   - Botón de copiar en cada campo individualmente
#   - Botón de acceso directo a edición
#
# Patrón: Mixin heredado por VaultApp.
# ══════════════════════════════════════════════════════════════════════════════

import tkinter as tk
 
from config.constants import COLORS, FONTS
 
 
class ViewDialogMixin:

    def _abrir_dialogo_ver(self):
        """
        Diálogo modal para ver los detalles de una entrada, incluyendo la contraseña.
        Permite copiar campos individuales con un click.
        """
        entrada = self._obtener_entrada_seleccionada()
        if not entrada:
            return

        dlg = tk.Toplevel(self.root)
        dlg.title(entrada.get("nombre", "Detalle"))
        dlg.configure(bg=COLORS["bg_dark"])
        dlg.resizable(False, False)
        dlg.grab_set()

        ancho, alto = 440, 460
        dlg.geometry(f"{ancho}x{alto}")
        self._centrar_ventana_hija(dlg, ancho, alto)

        # Título con el nombre del servicio
        tk.Label(
            dlg, text=f"🔑 {entrada.get('nombre', '')}",
            font=FONTS["title"], bg=COLORS["bg_dark"], fg=COLORS["text_primary"]
        ).pack(pady=(20, 4), padx=24, anchor="w")

        tk.Label(
            dlg, text=entrada.get("categoria", ""),
            font=FONTS["small"], bg=COLORS["bg_dark"], fg=COLORS["accent"]
        ).pack(padx=24, anchor="w", pady=(0, 16))

        frame = tk.Frame(dlg, bg=COLORS["bg_dark"])
        frame.pack(fill="both", expand=True, padx=24)

        def fila_copiable(parent, label, valor, oculto=False):
            """Helper: fila con label, valor y botón de copiar."""
            if not valor:
                return

            f = tk.Frame(parent, bg=COLORS["bg_panel"], pady=2)
            f.pack(fill="x", pady=3)

            tk.Label(f, text=label, font=FONTS["small"],
                     bg=COLORS["bg_panel"], fg=COLORS["text_secondary"],
                     width=12, anchor="w").pack(side="left", padx=(10,4), pady=6)

            # Valor (oculto para contraseña)
            var_mostrar_val = tk.BooleanVar(value=not oculto)
            texto_display = valor if not oculto else "●" * min(len(valor), 20)

            lbl_val = tk.Label(f, text=texto_display, font=FONTS["input"],
                               bg=COLORS["bg_panel"], fg=COLORS["text_primary"],
                               anchor="w")
            lbl_val.pack(side="left", fill="x", expand=True, padx=4, pady=6)

            # Botón mostrar/ocultar (solo para contraseña)
            if oculto:
                def toggle_val():
                    if var_mostrar_val.get():
                        lbl_val.config(text=valor)
                    else:
                        lbl_val.config(text="●" * min(len(valor), 20))
                tk.Checkbutton(
                    f, text="👁", variable=var_mostrar_val, command=toggle_val,
                    bg=COLORS["bg_panel"], selectcolor=COLORS["bg_input"],
                    activebackground=COLORS["bg_panel"],
                    font=("Segoe UI Emoji", 10)
                ).pack(side="left", padx=2)

            # Botón copiar
            def copiar(v=valor, l=label):
                dlg.clipboard_clear()
                dlg.clipboard_append(v)
                self._actualizar_estado(f"📋 {l} copiado")

            self._crear_boton_texto(f, "📋", copiar).pack(side="right", padx=6)

        # Mostrar todos los campos de la entrada
        fila_copiable(frame, "Usuario",    entrada.get("usuario",  ""))
        fila_copiable(frame, "Contraseña", entrada.get("password", ""), oculto=True)
        fila_copiable(frame, "URL",        entrada.get("url",      ""))
        fila_copiable(frame, "Notas",      entrada.get("notas",    ""))

        # Fechas
        tk.Label(
            frame,
            text=f"Creado: {entrada.get('creado','')[:10]}   |   "
                 f"Modificado: {entrada.get('modificado','')[:10]}",
            font=FONTS["small"], bg=COLORS["bg_dark"], fg=COLORS["text_dim"]
        ).pack(pady=(16, 0), anchor="w")

        # Botones
        frame_btns = tk.Frame(dlg, bg=COLORS["bg_dark"])
        frame_btns.pack(fill="x", padx=24, pady=16)

        self._crear_boton(
            frame_btns, "✏️ Editar",
            lambda: [dlg.destroy(), self._abrir_dialogo_editar()],
            color=COLORS["accent"]
        ).pack(side="right", ipady=8, padx=(6,0))

        self._crear_boton(frame_btns, "Cerrar", dlg.destroy, color=COLORS["bg_input"]).pack(
            side="right", ipady=8)


