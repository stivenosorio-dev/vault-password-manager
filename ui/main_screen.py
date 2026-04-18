# ══════════════════════════════════════════════════════════════════════════════
# Responsabilidad: pantalla principal después de desbloquear.
#   - Barra superior con botones de acción
#   - Campo de búsqueda en tiempo real
#   - Tabla (Treeview) con las entradas del vault
#   - Menú contextual (click derecho)
#   - Barra de estado inferior
#   - Acciones: copiar, eliminar, bloquear
#
# Patrón: Mixin heredado por VaultApp.
# ══════════════════════════════════════════════════════════════════════════════


import tkinter as tk
from tkinter import ttk, messagebox
 
from config.constants import COLORS, FONTS
 

class MainScreenMixin:

    def _mostrar_pantalla_principal(self):
        """
        Muestra la pantalla principal con la lista de entradas del vault.
        Contiene: barra superior, búsqueda, tabla de entradas y barra de estado.
        """
        # Limpiar ventana y reconfigurar tamaño
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.geometry("940x600")
        self.root.resizable(True, True)
        self._centrar_ventana(940, 600)

        # Desvincula Enter del desbloqueo
        self.root.unbind("<Return>")

        # ── Barra superior ────────────────────────────────────────────────────
        barra_top = tk.Frame(self.root, bg=COLORS["bg_panel"], height=60)
        barra_top.pack(fill="x", side="top")
        barra_top.pack_propagate(False)

        # Logo y título
        tk.Label(
            barra_top, text="🔐 VAULT", font=("Segoe UI", 14, "bold"),
            bg=COLORS["bg_panel"], fg=COLORS["gold"]
        ).pack(side="left", padx=20, pady=10)

        # Contador de entradas
        self.lbl_contador = tk.Label(
            barra_top, font=FONTS["small"],
            bg=COLORS["bg_panel"], fg=COLORS["text_secondary"]
        )
        self.lbl_contador.pack(side="left", padx=10)

        # Botones de la barra superior (derecha)
        self._crear_boton(
            barra_top, "＋ Nueva entrada",
            self._abrir_dialogo_nueva_entrada,
            color=COLORS["accent"]
        ).pack(side="right", padx=(5, 20), pady=10, ipady=6)

        self._crear_boton(
            barra_top, "🔑 Generar contraseña",
            self._abrir_generador,
            color=COLORS["bg_input"]
        ).pack(side="right", padx=5, pady=10, ipady=6)

        self._crear_boton(
            barra_top, "🔒 Bloquear",
            self._bloquear,
            color=COLORS["bg_input"]
        ).pack(side="right", padx=5, pady=10, ipady=6)

        from config.constants import THEMES, ACTIVE_THEME_NAME
        self.var_tema = tk.StringVar(value=ACTIVE_THEME_NAME)
        combo_tema = ttk.Combobox(
            barra_top, textvariable=self.var_tema, 
            values=list(THEMES.keys()),
            state="readonly", width=14, font=FONTS["small"]
        )
        combo_tema.pack(side="right", padx=(10, 5), pady=15)
        
        def al_cambiar_tema(event):
            self.cambiar_tema(self.var_tema.get())

        combo_tema.bind("<<ComboboxSelected>>", al_cambiar_tema)

        # ── Barra de búsqueda ─────────────────────────────────────────────────
        barra_busq = tk.Frame(self.root, bg=COLORS["bg_dark"], pady=10)
        barra_busq.pack(fill="x", padx=20)

        tk.Label(
            barra_busq, text="🔍", font=FONTS["icon"],
            bg=COLORS["bg_dark"], fg=COLORS["text_secondary"]
        ).pack(side="left")

        self.var_busqueda = tk.StringVar()
        self.var_busqueda.trace_add("write", lambda *_: self._filtrar_tabla())

        entry_busq = tk.Entry(
            barra_busq, textvariable=self.var_busqueda,
            font=FONTS["input"], width=35,
            bg=COLORS["bg_input"], fg=COLORS["text_primary"],
            insertbackground=COLORS["accent"],
            relief="flat", bd=6
        )
        entry_busq.pack(side="left", ipady=6, padx=(8, 0))
        entry_busq.insert(0, "")

        # Botón limpiar búsqueda
        self._crear_boton_texto(
            barra_busq, "✕",
            lambda: self.var_busqueda.set("")
        ).pack(side="left", padx=4)

        # ── Tabla de entradas ─────────────────────────────────────────────────
        frame_tabla = tk.Frame(self.root, bg=COLORS["bg_dark"])
        frame_tabla.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Scrollbar vertical
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        # Treeview (tabla)
        columnas = ("nombre", "usuario", "url", "categoria", "modificado")
        self.tabla = ttk.Treeview(
            frame_tabla,
            columns=columnas,
            show="headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse"
        )
        scrollbar.config(command=self.tabla.yview)

        # Configurar columnas
        self.tabla.heading("nombre",     text="Nombre / Servicio")
        self.tabla.heading("usuario",    text="Usuario / Email")
        self.tabla.heading("url",        text="URL")
        self.tabla.heading("categoria",  text="Categoría")
        self.tabla.heading("modificado", text="Modificado")

        self.tabla.column("nombre",     width=200, minwidth=120)
        self.tabla.column("usuario",    width=220, minwidth=120)
        self.tabla.column("url",        width=180, minwidth=100)
        self.tabla.column("categoria",  width=100, minwidth=80)
        self.tabla.column("modificado", width=130, minwidth=100)

        self.tabla.pack(fill="both", expand=True)

        # Eventos de la tabla
        self.tabla.bind("<Double-1>",   lambda e: self._abrir_dialogo_ver())
        self.tabla.bind("<Delete>",     lambda e: self._eliminar_entrada())
        self.tabla.bind("<Return>",     lambda e: self._abrir_dialogo_ver())

        # Menú contextual (click derecho)
        self.menu_contexto = tk.Menu(self.root, tearoff=0,
            bg=COLORS["bg_panel"], fg=COLORS["text_primary"],
            activebackground=COLORS["accent"], activeforeground=COLORS["text_primary"])
        self.menu_contexto.add_command(label="👁  Ver / Editar",      command=self._abrir_dialogo_ver)
        self.menu_contexto.add_command(label="📋 Copiar contraseña",  command=self._copiar_password_seleccionada)
        self.menu_contexto.add_command(label="📋 Copiar usuario",     command=self._copiar_usuario_seleccionado)
        self.menu_contexto.add_separator()
        self.menu_contexto.add_command(label="✏️  Editar",             command=self._abrir_dialogo_editar)
        self.menu_contexto.add_separator()
        self.menu_contexto.add_command(label="🗑  Eliminar",          command=self._eliminar_entrada)
        self.tabla.bind("<Button-3>", self._mostrar_menu_contexto)

        # ── Barra de estado (inferior) ────────────────────────────────────────
        barra_estado = tk.Frame(self.root, bg=COLORS["bg_panel"], height=28)
        barra_estado.pack(fill="x", side="bottom")
        barra_estado.pack_propagate(False)

        self.lbl_estado = tk.Label(
            barra_estado, font=FONTS["small"],
            bg=COLORS["bg_panel"], fg=COLORS["text_secondary"]
        )
        self.lbl_estado.pack(side="left", padx=15, pady=5)

        tk.Label(
            barra_estado,
            text=f"📁 {self.storage.ruta}",
            font=FONTS["small"],
            bg=COLORS["bg_panel"], fg=COLORS["text_dim"]
        ).pack(side="right", padx=15, pady=5)

        # Cargar datos iniciales en la tabla
        self._refrescar_tabla()

    def _refrescar_tabla(self, entradas: list[dict] | None = None):
        """
        Recarga la tabla con las entradas del vault.

        Args:
            entradas: lista a mostrar (None = usar self.entradas completa)
        """
        # Limpiar tabla
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        lista_activos = [e for e in self.entradas if e.get("estado", "activo") == "activo"]
        lista = entradas if entradas is not None else lista_activos

        # Insertar entradas con filas alternas
        for i, e in enumerate(lista):
            tag = "par" if i % 2 == 0 else "impar"
            self.tabla.insert("", "end", iid=e["id"], values=(
                e.get("nombre",    ""),
                e.get("usuario",   ""),
                e.get("url",       ""),
                e.get("categoria", ""),
                e.get("modificado", "")[:10],   # Solo la fecha, sin hora
            ), tags=(tag,))

        # Estilos de filas alternas
        self.tabla.tag_configure("par",   background=COLORS["bg_row"])
        self.tabla.tag_configure("impar", background=COLORS["bg_row_alt"])

        # Actualizar contador
        total = len(lista_activos)
        mostrando = len(lista)
        if mostrando == total:
            self.lbl_contador.config(text=f"{total} entrada{'s' if total != 1 else ''}")
        else:
            self.lbl_contador.config(text=f"Mostrando {mostrando} de {total}")

        self._actualizar_estado(f"Vault desbloqueado · {total} entradas guardadas")

    def _filtrar_tabla(self):
        """Filtra las entradas de la tabla según el texto de búsqueda."""
        query = self.var_busqueda.get().strip().lower()

        if not query:
            self._refrescar_tabla()
            return

        # Busca en nombre, usuario, URL, notas y categoría
        filtradas = [
            e for e in self.entradas
            if e.get("estado", "activo") == "activo" and (
               query in e.get("nombre",    "").lower()
            or query in e.get("usuario",   "").lower()
            or query in e.get("url",       "").lower()
            or query in e.get("notas",     "").lower()
            or query in e.get("categoria", "").lower()
            )
        ]
        self._refrescar_tabla(filtradas)

    def _mostrar_menu_contexto(self, event):
        """Muestra el menú contextual al hacer click derecho en la tabla."""
        item = self.tabla.identify_row(event.y)
        if item:
            self.tabla.selection_set(item)
            self.menu_contexto.post(event.x_root, event.y_root)

    def _obtener_entrada_seleccionada(self) -> dict | None:
        """
        Retorna el dict de la entrada actualmente seleccionada en la tabla.

        Retorna:
            dict con los datos de la entrada, o None si no hay selección
        """
        sel = self.tabla.selection()
        if not sel:
            return None
        id_sel = sel[0]
        return next((e for e in self.entradas if e["id"] == id_sel), None)

    def _copiar_password_seleccionada(self):
        """Copia la contraseña de la entrada seleccionada al portapapeles."""
        entrada = self._obtener_entrada_seleccionada()
        if entrada:
            self.root.clipboard_clear()
            self.root.clipboard_append(entrada.get("password", ""))
            self._actualizar_estado("✅ Contraseña copiada al portapapeles")

    def _copiar_usuario_seleccionado(self):
        """Copia el usuario de la entrada seleccionada al portapapeles."""
        entrada = self._obtener_entrada_seleccionada()
        if entrada:
            self.root.clipboard_clear()
            self.root.clipboard_append(entrada.get("usuario", ""))
            self._actualizar_estado("✅ Usuario copiado al portapapeles")

    def _bloquear(self):
        """Bloquea el vault limpiando la sesión y volviendo a la pantalla de desbloqueo."""
        self.clave    = None
        self.password = ""
        self.entradas = []
        self._mostrar_pantalla_desbloqueo()

    def _eliminar_entrada(self):
        """Elimina la entrada seleccionada después de confirmación."""
        entrada = self._obtener_entrada_seleccionada()
        if not entrada:
            return

        confirmar = messagebox.askyesno(
            "Eliminar entrada",
            f"¿Mover '{entrada.get('nombre', '')}' a la papelera (inactiva)?"
        )
        if confirmar:
            entrada["estado"] = "inactivo"
            self._guardar_vault()
            self._refrescar_tabla()
            self._actualizar_estado(f"🗑 '{entrada['nombre']}' eliminada (inactiva)")

    def _actualizar_estado(self, mensaje: str):
        """Actualiza el texto de la barra de estado."""
        if hasattr(self, "lbl_estado"):
            self.lbl_estado.config(text=mensaje)
