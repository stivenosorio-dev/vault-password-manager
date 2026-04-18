# ══════════════════════════════════════════════════════════════════════════════
# VaultApp — Orquestador principal de la interfaz gráfica
# ══════════════════════════════════════════════════════════════════════════════
# Responsabilidad:
#   - Inicializar la ventana raíz y el estado de sesión
#   - Combinar todos los Mixins mediante herencia múltiple
#   - Proveer los métodos utilitarios compartidos por todos los Mixins:
#       _crear_boton(), _crear_boton_texto(), _configurar_estilos(),
#       _centrar_ventana(), _centrar_ventana_hija(), _guardar_vault()
#
# Patrón: Herencia múltiple (Mixins).
#   VaultApp hereda de todos los Mixins y los une en una sola clase.
#   Cada Mixin es independiente pero comparte 'self' a través de VaultApp.
#
# Diagrama de herencia:
#   VaultApp
#   ├── UnlockMixin       (ui/unlock_screen.py)
#   ├── MainScreenMixin   (ui/main_screen.py)
#   ├── EntryDialogMixin  (ui/entry_dialog.py)
#   ├── ViewDialogMixin   (ui/view_dialog.py)
#   └── GeneratorMixin    (ui/generator_dialog.py)
# ══════════════════════════════════════════════════════════════════════════════
 
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
 
from config.constants import COLORS, FONTS, VAULT_FILENAME
from storage.vault_storage import VaultStorage
 
# Importar todos los Mixins de UI
from ui.unlock_screen    import UnlockMixin
from ui.main_screen      import MainScreenMixin
from ui.entry_dialog     import EntryDialogMixin
from ui.view_dialog      import ViewDialogMixin
from ui.generator_dialog import GeneratorMixin
 
 
class VaultApp(UnlockMixin, MainScreenMixin, EntryDialogMixin, ViewDialogMixin, GeneratorMixin):
    
    
    def __init__(self, root: tk.Tk):
        """
        Inicializa la aplicación y configura la ventana raíz.

        Args:
            root: ventana principal de Tkinter
        """
        self.root = root
        self.root.title("Vault — Contraseñas Seguras")
        self.root.resizable(True, True)
        self.root.minsize(780, 500)

        # Centrar ventana en pantalla
        self._centrar_ventana(900, 600)

        # Configurar fondo global
        self.root.configure(bg=COLORS["bg_dark"])

        # Estado de sesión — inicialmente vacío
        self.clave:    bytes | None = None
        self.password: str          = ""
        self.entradas: list[dict]   = []
        self.entrada_visible: str | None = None   # ID de la entrada que muestra contraseña

        # Instancia de almacenamiento (archivo en la misma carpeta que el script)
        script_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
        self.storage = VaultStorage(str(script_dir / VAULT_FILENAME))

        # Aplicar estilos ttk globales
        self._configurar_estilos()

        # Mostrar pantalla inicial
        self._mostrar_pantalla_desbloqueo()

    def _guardar_vault(self):
        """Persiste el estado actual del vault en disco."""
        ok = self.storage.guardar_entradas(self.entradas, self.clave, self.password)
        if not ok:
            messagebox.showerror("Error", "No se pudo guardar el vault en disco.")

    def _crear_boton(self, parent, texto: str, comando, color: str, ancho: int = None) -> tk.Button:
        """
        Crea un botón estilizado con hover. Se ajusta automáticamente al texto salvo que se especifique ancho.

        Args:
            parent:  widget padre
            texto:   texto del botón
            comando: función a ejecutar al hacer click
            color:   color de fondo
            ancho:   ancho en caracteres (opcional)

        Retorna:
            tk.Button configurado
        """
        btn_kwargs = {
            "text": texto, "command": comando,
            "font": FONTS["button"],
            "bg": color, "fg": COLORS["text_primary"],
            "activebackground": COLORS["accent_hover"],
            "activeforeground": COLORS["text_primary"],
            "relief": "flat", "bd": 0, "cursor": "hand2",
            "padx": 14, "pady": 4
        }
        if ancho is not None:
            btn_kwargs["width"] = ancho
            
        btn = tk.Button(parent, **btn_kwargs)
        # Efectos hover
        btn.bind("<Enter>", lambda e: btn.config(bg=COLORS["accent_hover"]))
        btn.bind("<Leave>", lambda e: btn.config(bg=color))
        return btn

    def _crear_boton_texto(self, parent, texto: str, comando) -> tk.Button:
        """Crea un botón de texto plano sin fondo (estilo link)."""
        btn = tk.Button(
            parent, text=texto, command=comando,
            font=FONTS["small"],
            bg=COLORS["bg_dark"], fg=COLORS["text_secondary"],
            activebackground=COLORS["bg_dark"],
            activeforeground=COLORS["accent"],
            relief="flat", bd=0, cursor="hand2"
        )
        btn.bind("<Enter>", lambda e: btn.config(fg=COLORS["accent"]))
        btn.bind("<Leave>", lambda e: btn.config(fg=COLORS["text_secondary"]))
        return btn

    def cambiar_tema(self, nombre_tema: str):
        from config.constants import set_active_theme, COLORS
        set_active_theme(nombre_tema)
        self.root.configure(bg=COLORS["bg_dark"])
        self._configurar_estilos()
        if hasattr(self, 'clave') and self.clave is not None:
            self._mostrar_pantalla_principal()
        else:
            self._mostrar_pantalla_desbloqueo()

    def _configurar_estilos(self):
        """Configura los estilos de ttk (Treeview, Combobox, Scrollbar)."""
        style = ttk.Style()
        style.theme_use("clam")

        # Treeview — tabla principal
        style.configure("Treeview",
            background=COLORS["bg_row"],
            foreground=COLORS["text_primary"],
            fieldbackground=COLORS["bg_row"],
            rowheight=32,
            font=FONTS["table"],
            borderwidth=0,
            relief="flat"
        )
        style.configure("Treeview.Heading",
            background=COLORS["bg_panel"],
            foreground=COLORS["text_secondary"],
            font=FONTS["label_bold"],
            relief="flat",
            borderwidth=0
        )
        style.map("Treeview",
            background=[("selected", COLORS["bg_row_sel"])],
            foreground=[("selected", COLORS["text_primary"])]
        )

        # Scrollbar
        style.configure("Vertical.TScrollbar",
            background=COLORS["bg_panel"],
            troughcolor=COLORS["bg_dark"],
            bordercolor=COLORS["bg_dark"],
            arrowcolor=COLORS["text_secondary"]
        )

        # Combobox
        style.configure("TCombobox",
            fieldbackground=COLORS["bg_input"],
            background=COLORS["bg_input"],
            foreground=COLORS["text_primary"],
            selectbackground=COLORS["accent"]
        )

    def _centrar_ventana(self, ancho: int, alto: int):
        """Centra la ventana principal en la pantalla."""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  // 2) - (ancho // 2)
        y = (self.root.winfo_screenheight() // 2) - (alto  // 2)
        self.root.geometry(f"{ancho}x{alto}+{x}+{y}")

    def _centrar_ventana_hija(self, ventana: tk.Toplevel, ancho: int, alto: int):
        """Centra una ventana hija (Toplevel) relativa a la ventana principal."""
        ventana.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width()  // 2) - (ancho // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (alto  // 2)
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

