# ══════════════════════════════════════════════════════════════════════════════
# Responsabilidad: formulario modal para crear o editar una entrada del vault.
#   - Campos: nombre, usuario, contraseña, URL, notas, categoría
#   - Generador de contraseña integrado en el campo
#   - Validación de campos obligatorios
#   - Diferencia entre modo creación y modo edición
#
# Patrón: Mixin heredado por VaultApp.
# ══════════════════════════════════════════════════════════════════════════════


import secrets
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
 
from config.constants import COLORS, FONTS
 
 
class EntryDialogMixin:

    def _abrir_dialogo_nueva_entrada(self):
        """Abre el diálogo para crear una nueva entrada."""
        self._abrir_dialogo_entrada(entrada_existente=None)

    def _abrir_dialogo_editar(self):
        """Abre el diálogo para editar la entrada seleccionada."""
        entrada = self._obtener_entrada_seleccionada()
        if entrada:
            self._abrir_dialogo_entrada(entrada_existente=entrada)

    def _abrir_dialogo_entrada(self, entrada_existente: dict | None):
        """
        Diálogo modal para crear o editar una entrada del vault.

        Args:
            entrada_existente: dict de la entrada a editar, o None para nueva
        """
        es_edicion = entrada_existente is not None

        dlg = tk.Toplevel(self.root)
        dlg.title("Editar entrada" if es_edicion else "Nueva entrada")
        dlg.configure(bg=COLORS["bg_dark"])
        dlg.resizable(False, False)
        dlg.grab_set()   # Modal

        ancho, alto = 500, 800
        dlg.geometry(f"{ancho}x{alto}")
        self._centrar_ventana_hija(dlg, ancho, alto)

        # ── Título del diálogo ──
        tk.Label(
            dlg,
            text="✏️  Editar entrada" if es_edicion else "＋  Nueva entrada",
            font=FONTS["title"], bg=COLORS["bg_dark"], fg=COLORS["text_primary"]
        ).pack(pady=(20, 16), padx=24, anchor="w")

        # ── Frame de campos ──
        frame = tk.Frame(dlg, bg=COLORS["bg_dark"])
        frame.pack(fill="both", expand=True, padx=24)

        def campo(parent, label, valor="", es_password=False, ancho=38):
            """Helper local: crea un par label + entry."""
            tk.Label(parent, text=label, font=FONTS["label_bold"],
                     bg=COLORS["bg_dark"], fg=COLORS["text_secondary"]).pack(anchor="w", pady=(8,2))
            show = "●" if es_password else ""
            e = tk.Entry(parent, show=show, font=FONTS["input"], width=ancho,
                         bg=COLORS["bg_input"], fg=COLORS["text_primary"],
                         insertbackground=COLORS["accent"], relief="flat", bd=6)
            e.pack(fill="x", ipady=7)
            if valor:
                e.insert(0, valor)
            return e

        # Campos del formulario (pre-llenados si es edición)
        ev = entrada_existente or {}
        e_nombre    = campo(frame, "Nombre / Servicio *", ev.get("nombre", ""))
        e_usuario   = campo(frame, "Usuario / Email *",   ev.get("usuario", ""))

        # Contraseña con botón de mostrar/ocultar y generador
        tk.Label(frame, text="Contraseña *", font=FONTS["label_bold"],
                 bg=COLORS["bg_dark"], fg=COLORS["text_secondary"]).pack(anchor="w", pady=(8,2))

        frame_pwd = tk.Frame(frame, bg=COLORS["bg_dark"])
        frame_pwd.pack(fill="x")

        e_pwd = tk.Entry(frame_pwd, show="●", font=FONTS["input"],
                         bg=COLORS["bg_input"], fg=COLORS["text_primary"],
                         insertbackground=COLORS["accent"], relief="flat", bd=6)
        e_pwd.pack(side="left", fill="x", expand=True, ipady=7)
        if ev.get("password"):
            e_pwd.insert(0, ev["password"])

        # Botón ojo (mostrar/ocultar contraseña en el campo)
        var_ojo = tk.BooleanVar(value=False)
        def toggle_ojo():
            e_pwd.config(show="" if var_ojo.get() else "●")
        tk.Checkbutton(
            frame_pwd, text="👁", variable=var_ojo, command=toggle_ojo,
            bg=COLORS["bg_dark"], fg=COLORS["text_secondary"],
            selectcolor=COLORS["bg_input"], activebackground=COLORS["bg_dark"],
            font=("Segoe UI Emoji", 12)
        ).pack(side="left", padx=(6,0))

        # Botón generar contraseña segura
        def generar_y_pegar():
            pwd_gen = self._generar_password()
            e_pwd.delete(0, "end")
            e_pwd.insert(0, pwd_gen)
            var_ojo.set(True)
            e_pwd.config(show="")

        self._crear_boton_texto(frame_pwd, "⚙ Generar", generar_y_pegar).pack(side="left", padx=4)

        e_url      = campo(frame, "URL (opcional)",      ev.get("url", ""))
        e_notas    = campo(frame, "Notas (opcional)",    ev.get("notas", ""))

        # Categoría como Combobox
        tk.Label(frame, text="Categoría", font=FONTS["label_bold"],
                 bg=COLORS["bg_dark"], fg=COLORS["text_secondary"]).pack(anchor="w", pady=(8,2))

        categorias = ["Personal", "Trabajo", "Redes Sociales", "Banco / Finanzas",
                      "Desarrollo", "Email", "Streaming", "Gaming", "Otro"]
        var_cat = tk.StringVar(value=ev.get("categoria", "Personal"))
        combo = ttk.Combobox(frame, textvariable=var_cat, values=categorias,
                              font=FONTS["input"], state="normal")
        combo.pack(fill="x", ipady=6)

        # ── Botones de acción ──
        frame_btns = tk.Frame(dlg, bg=COLORS["bg_dark"])
        frame_btns.pack(fill="x", padx=24, pady=16)

        def guardar():
            nombre  = e_nombre.get().strip()
            usuario = e_usuario.get().strip()
            pwd     = e_pwd.get()

            if not nombre or not usuario or not pwd:
                messagebox.showwarning("Campos requeridos",
                    "Nombre, usuario y contraseña son obligatorios.", parent=dlg)
                return

            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if es_edicion:
                # Actualizar entrada existente
                for e in self.entradas:
                    if e["id"] == entrada_existente["id"]:
                        e["nombre"]    = nombre
                        e["usuario"]   = usuario
                        e["password"]  = pwd
                        e["url"]       = e_url.get().strip()
                        e["notas"]     = e_notas.get().strip()
                        e["categoria"] = var_cat.get()
                        e["modificado"]= ahora
                        break
                self._actualizar_estado(f"✅ '{nombre}' actualizada")
            else:
                # Nueva entrada con ID único basado en timestamp + random
                nueva = {
                    "id":         secrets.token_hex(8),
                    "nombre":     nombre,
                    "usuario":    usuario,
                    "password":   pwd,
                    "url":        e_url.get().strip(),
                    "notas":      e_notas.get().strip(),
                    "categoria":  var_cat.get(),
                    "estado":     "activo",
                    "creado":     ahora,
                    "modificado": ahora,
                }
                self.entradas.append(nueva)
                self._actualizar_estado(f"✅ '{nombre}' agregada")

            self._guardar_vault()
            self._refrescar_tabla()
            dlg.destroy()

        self._crear_boton(frame_btns, "💾 Guardar", guardar, color=COLORS["accent"]).pack(
            side="right", ipady=8, padx=(6,0))
        self._crear_boton(frame_btns, "Cancelar", dlg.destroy, color=COLORS["bg_input"]).pack(
            side="right", ipady=8)
