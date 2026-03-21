"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    VAULT — Manejador de Contraseñas Seguro                 ║
║                         Autor: Jorge Stiven Osorio                         ║
║                                                                              ║
║  Arquitectura (todo en main.py, preparado para modularización futura):      ║
║  ─────────────────────────────────────────────────────────────────────────  ║
║  [SECCIÓN 1]  Imports y constantes globales                                 ║
║  [SECCIÓN 2]  CryptoManager   — encriptación/desencriptación (Fernet)       ║
║  [SECCIÓN 3]  VaultStorage    — lectura/escritura del archivo .vault        ║
║  [SECCIÓN 4]  VaultApp        — interfaz gráfica completa (Tkinter)         ║
║    [4.1]        Pantalla de desbloqueo (master password)                    ║
║    [4.2]        Pantalla principal (CRUD de entradas)                       ║
║    [4.3]        Diálogo de nueva/editar entrada                             ║
║    [4.4]        Diálogo de ver contraseña                                   ║
║  [SECCIÓN 5]  Punto de entrada principal                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

DEPENDENCIAS EXTERNAS (instalar una sola vez):
    pip install cryptography

DEPENDENCIAS ESTÁNDAR (incluidas en Python):
    tkinter, json, os, base64, hashlib, secrets, sys, pathlib, datetime

ARCHIVO DE DATOS:
    vault.vault — generado automáticamente en la misma carpeta del script.
    Puedes copiar este archivo a Google Drive para respaldo.
    Sin la contraseña maestra correcta, el contenido es ilegible.

PARA CONVERTIR A EJECUTABLE PORTABLE (.exe):
    pip install pyinstaller
    pyinstaller --onefile --windowed --name=Vault main.py
    El .exe quedará en la carpeta dist/
"""

# ══════════════════════════════════════════════════════════════════════════════
# [SECCIÓN 1] IMPORTS Y CONSTANTES GLOBALES
# ══════════════════════════════════════════════════════════════════════════════

import os
import sys
import json
import base64
import hashlib
import secrets
import string
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime

from config.constants import COLORS, FONTS, VAULT_FILENAME, PBKDF2_ITERATIONS, SALT_SIZE, VAULT_VERSION

# Importación de cryptography (Fernet — encriptación simétrica AES-128 en CBC)
# Si no está instalada, el programa avisa claramente.
try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:
    import subprocess
    print("Instalando dependencias necesarias...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# ══════════════════════════════════════════════════════════════════════════════
# [SECCIÓN 2] CRYPTO MANAGER
# ══════════════════════════════════════════════════════════════════════════════
# Responsabilidad: todo lo relacionado con encriptación y hash.
# Futura extracción: crypto/manager.py
#
# Algoritmo usado:
#   - PBKDF2-HMAC-SHA256: deriva una clave de 32 bytes desde la contraseña maestra
#   - Fernet (AES-128-CBC + HMAC-SHA256): encripta/desencripta los datos del vault
#
# Por qué Fernet:
#   - Incluye autenticación del mensaje (HMAC) — detecta datos corruptos o alterados
#   - Usa IV aleatorio en cada encriptación — mismo texto = diferente cifrado
#   - Estándar de la librería cryptography de Python — auditado y confiable

class CryptoManager:
    """
    Maneja toda la criptografía del vault.

    Flujo de encriptación:
        contraseña_maestra + salt → PBKDF2 → clave_fernet → Fernet.encrypt(datos)

    Flujo de desencriptación:
        contraseña_maestra + salt (leído del vault) → PBKDF2 → clave_fernet → Fernet.decrypt(datos)
    """

    @staticmethod
    def generar_salt() -> bytes:
        """
        Genera un salt aleatorio criptográficamente seguro.
        El salt evita ataques de diccionario y rainbow tables.
        Cada vault tiene su propio salt único.

        Retorna:
            bytes: salt de SALT_SIZE bytes
        """
        return secrets.token_bytes(SALT_SIZE)

    @staticmethod
    def derivar_clave(password: str, salt: bytes) -> bytes:
        """
        Deriva una clave de encriptación de 32 bytes desde la contraseña maestra.
        Usa PBKDF2-HMAC-SHA256 con PBKDF2_ITERATIONS iteraciones.

        Args:
            password: contraseña maestra en texto plano
            salt:     salt único del vault

        Retorna:
            bytes: clave de 32 bytes (256 bits) compatible con Fernet
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )
        # Fernet requiere la clave en base64 URL-safe
        return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))

    @staticmethod
    def encriptar(datos: str, clave: bytes) -> bytes:
        """
        Encripta un string usando Fernet (AES-128-CBC + HMAC-SHA256).

        Args:
            datos: texto en claro a encriptar
            clave: clave derivada por derivar_clave()

        Retorna:
            bytes: datos encriptados (token Fernet)
        """
        f = Fernet(clave)
        return f.encrypt(datos.encode("utf-8"))

    @staticmethod
    def desencriptar(token: bytes, clave: bytes) -> str | None:
        """
        Desencripta un token Fernet.

        Args:
            token: datos encriptados (token Fernet)
            clave: clave derivada (debe ser la misma que encriptó)

        Retorna:
            str: datos en claro, o None si la clave es incorrecta
        """
        try:
            f = Fernet(clave)
            return f.decrypt(token).decode("utf-8")
        except InvalidToken:
            # Clave incorrecta o datos corruptos
            return None

    @staticmethod
    def hash_verificacion(password: str, salt: bytes) -> str:
        """
        Genera un hash de verificación de la contraseña maestra.
        Se guarda en el vault para verificar si la contraseña es correcta
        ANTES de intentar desencriptar todos los datos.

        Usa PBKDF2-HMAC-SHA256 con un salt distinto (salt + b"verify").

        Args:
            password: contraseña maestra
            salt:     salt del vault

        Retorna:
            str: hash hex de 64 caracteres
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt + b"verify",   # Salt modificado para que el hash sea diferente a la clave
            iterations=PBKDF2_ITERATIONS,
        )
        return kdf.derive(password.encode("utf-8")).hex()


# ══════════════════════════════════════════════════════════════════════════════
# [SECCIÓN 3] VAULT STORAGE
# ══════════════════════════════════════════════════════════════════════════════
# Responsabilidad: leer y escribir el archivo .vault en disco.
# Futura extracción: storage/vault_storage.py
#
# Estructura del archivo .vault (JSON antes de encriptar):
# {
#   "version":      "1.0",
#   "salt":         "<salt en base64>",
#   "hash_verify":  "<hash de verificación de contraseña>",
#   "data":         "<datos encriptados en base64>"
# }
#
# Los "data" contienen, antes de encriptar, un JSON con la lista de entradas:
# [
#   {
#     "id":         "uuid único",
#     "nombre":     "Google",
#     "usuario":    "usuario@gmail.com",
#     "password":   "contraseña real",
#     "url":        "https://google.com",
#     "notas":      "...",
#     "categoria":  "Personal",
#     "creado":     "2024-01-15 10:30:00",
#     "modificado": "2024-01-15 10:30:00"
#   },
#   ...
# ]

class VaultStorage:
    """
    Maneja la persistencia del vault en disco.
    El archivo .vault es un JSON con metadatos + datos encriptados.
    """

    def __init__(self, ruta_archivo: str = VAULT_FILENAME):
        """
        Args:
            ruta_archivo: ruta al archivo .vault (por defecto, misma carpeta del script)
        """
        self.ruta = Path(ruta_archivo)

    def existe(self) -> bool:
        """Verifica si ya existe un archivo vault."""
        return self.ruta.exists()

    def crear_vault(self, password: str) -> bytes:
        """
        Crea un vault nuevo con contraseña maestra.
        Guarda el archivo con lista de entradas vacía encriptada.

        Args:
            password: contraseña maestra elegida por el usuario

        Retorna:
            bytes: clave Fernet derivada (para usarla en la sesión)
        """
        salt = CryptoManager.generar_salt()
        clave = CryptoManager.derivar_clave(password, salt)
        hash_v = CryptoManager.hash_verificacion(password, salt)

        # Lista vacía de entradas como punto de partida
        datos_iniciales = json.dumps([], ensure_ascii=False)
        datos_enc = CryptoManager.encriptar(datos_iniciales, clave)

        vault_json = {
            "version":     VAULT_VERSION,
            "salt":        base64.b64encode(salt).decode(),
            "hash_verify": hash_v,
            "data":        base64.b64encode(datos_enc).decode(),
        }

        self._escribir_archivo(vault_json)
        return clave

    def verificar_password(self, password: str) -> tuple[bool, bytes | None]:
        """
        Verifica si la contraseña es correcta comparando el hash de verificación.

        Args:
            password: contraseña a verificar

        Retorna:
            tuple: (es_correcta: bool, clave: bytes | None)
                   La clave se retorna si es correcta, para reutilizarla en la sesión.
        """
        vault_json = self._leer_archivo()
        if vault_json is None:
            return False, None

        salt = base64.b64decode(vault_json["salt"])
        hash_esperado = vault_json["hash_verify"]
        hash_ingresado = CryptoManager.hash_verificacion(password, salt)

        if hash_ingresado == hash_esperado:
            clave = CryptoManager.derivar_clave(password, salt)
            return True, clave
        return False, None

    def cargar_entradas(self, clave: bytes) -> list[dict]:
        """
        Carga y desencripta la lista de entradas del vault.

        Args:
            clave: clave Fernet de la sesión actual

        Retorna:
            list[dict]: lista de entradas, o [] si hay error
        """
        vault_json = self._leer_archivo()
        if vault_json is None:
            return []

        datos_enc = base64.b64decode(vault_json["data"])
        datos_plano = CryptoManager.desencriptar(datos_enc, clave)

        if datos_plano is None:
            return []

        return json.loads(datos_plano)

    def guardar_entradas(self, entradas: list[dict], clave: bytes, password: str) -> bool:
        """
        Encripta y guarda la lista de entradas en el vault.

        Args:
            entradas: lista actualizada de entradas
            clave:    clave Fernet de la sesión
            password: contraseña maestra (para regenerar hash de verificación)

        Retorna:
            bool: True si se guardó correctamente
        """
        try:
            vault_json = self._leer_archivo()
            salt = base64.b64decode(vault_json["salt"])
            hash_v = CryptoManager.hash_verificacion(password, salt)

            datos_plano = json.dumps(entradas, ensure_ascii=False, indent=2)
            datos_enc = CryptoManager.encriptar(datos_plano, clave)

            vault_json_nuevo = {
                "version":     VAULT_VERSION,
                "salt":        base64.b64encode(salt).decode(),
                "hash_verify": hash_v,
                "data":        base64.b64encode(datos_enc).decode(),
            }

            self._escribir_archivo(vault_json_nuevo)
            return True
        except Exception as e:
            print(f"Error al guardar: {e}")
            return False

    def cambiar_ruta(self, nueva_ruta: str):
        """
        Cambia la ruta del archivo vault (para abrir un vault de Drive, por ejemplo).

        Args:
            nueva_ruta: nueva ruta al archivo .vault
        """
        self.ruta = Path(nueva_ruta)

    # ── Métodos privados de I/O ───────────────────────────────────────────────

    def _leer_archivo(self) -> dict | None:
        """Lee y parsea el archivo .vault como JSON."""
        try:
            with open(self.ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _escribir_archivo(self, datos: dict):
        """Escribe el JSON del vault al archivo en disco."""
        with open(self.ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# [SECCIÓN 4] VAULT APP — INTERFAZ GRÁFICA
# ══════════════════════════════════════════════════════════════════════════════
# Responsabilidad: toda la UI en Tkinter.
# Futura extracción:
#   ui/unlock_screen.py    → [4.1] Pantalla de desbloqueo
#   ui/main_screen.py      → [4.2] Pantalla principal
#   ui/entry_dialog.py     → [4.3] Diálogo nueva/editar entrada
#   ui/view_dialog.py      → [4.4] Diálogo de ver contraseña

class VaultApp:
    """
    Aplicación principal. Orquesta todas las pantallas y el estado de la sesión.

    Estado de sesión (atributos de instancia):
        self.clave:    bytes — clave Fernet activa (None si no se ha desbloqueado)
        self.password: str   — contraseña maestra de la sesión (para re-guardar)
        self.entradas: list  — lista de dicts con las entradas del vault
        self.storage:  VaultStorage — instancia de almacenamiento
    """

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

    # ──────────────────────────────────────────────────────────────────────────
    # [4.1] PANTALLA DE DESBLOQUEO
    # ──────────────────────────────────────────────────────────────────────────

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

    # ──────────────────────────────────────────────────────────────────────────
    # [4.2] PANTALLA PRINCIPAL
    # ──────────────────────────────────────────────────────────────────────────

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

        lista = entradas if entradas is not None else self.entradas

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
        total = len(self.entradas)
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
            if query in e.get("nombre",    "").lower()
            or query in e.get("usuario",   "").lower()
            or query in e.get("url",       "").lower()
            or query in e.get("notas",     "").lower()
            or query in e.get("categoria", "").lower()
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
            f"¿Eliminar '{entrada.get('nombre', '')}' permanentemente?\n\nEsta acción no se puede deshacer."
        )
        if confirmar:
            self.entradas = [e for e in self.entradas if e["id"] != entrada["id"]]
            self._guardar_vault()
            self._refrescar_tabla()
            self._actualizar_estado(f"🗑 '{entrada['nombre']}' eliminada")

    def _actualizar_estado(self, mensaje: str):
        """Actualiza el texto de la barra de estado."""
        if hasattr(self, "lbl_estado"):
            self.lbl_estado.config(text=mensaje)

    # ──────────────────────────────────────────────────────────────────────────
    # [4.3] DIÁLOGO DE NUEVA / EDITAR ENTRADA
    # ──────────────────────────────────────────────────────────────────────────

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

    # ──────────────────────────────────────────────────────────────────────────
    # [4.4] DIÁLOGO DE VER ENTRADA
    # ──────────────────────────────────────────────────────────────────────────

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

    # ──────────────────────────────────────────────────────────────────────────
    # GENERADOR DE CONTRASEÑAS
    # ──────────────────────────────────────────────────────────────────────────

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
        dlg.geometry("400x280")
        self._centrar_ventana_hija(dlg, 400, 280)

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

    # ──────────────────────────────────────────────────────────────────────────
    # UTILIDADES DE UI
    # ──────────────────────────────────────────────────────────────────────────

    def _guardar_vault(self):
        """Persiste el estado actual del vault en disco."""
        ok = self.storage.guardar_entradas(self.entradas, self.clave, self.password)
        if not ok:
            messagebox.showerror("Error", "No se pudo guardar el vault en disco.")

    def _crear_boton(self, parent, texto: str, comando, color: str, ancho: int = 16) -> tk.Button:
        """
        Crea un botón estilizado con hover.

        Args:
            parent:  widget padre
            texto:   texto del botón
            comando: función a ejecutar al hacer click
            color:   color de fondo
            ancho:   ancho en caracteres

        Retorna:
            tk.Button configurado
        """
        btn = tk.Button(
            parent, text=texto, command=comando,
            font=FONTS["button"], width=ancho,
            bg=color, fg=COLORS["text_primary"],
            activebackground=COLORS["accent_hover"],
            activeforeground=COLORS["text_primary"],
            relief="flat", bd=0, cursor="hand2"
        )
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
            font=FONTS["table"]
        )
        style.configure("Treeview.Heading",
            background=COLORS["bg_panel"],
            foreground=COLORS["text_secondary"],
            font=FONTS["label_bold"],
            relief="flat"
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


# ══════════════════════════════════════════════════════════════════════════════
# [SECCIÓN 5] PUNTO DE ENTRADA PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """
    Punto de entrada de la aplicación.
    Crea la ventana raíz de Tkinter e inicia el loop de eventos.
    """
    root = tk.Tk()

    # Ocultar la ventana mientras carga (evita flash blanco)
    root.withdraw()

    # Icono de la ventana (emoji como fallback — en .exe usar un .ico real)
    try:
        root.iconbitmap("vault.ico")
    except Exception:
        pass   # Sin icono si no existe el archivo

    # Iniciar la aplicación
    app = VaultApp(root)

    # Mostrar ventana
    root.deiconify()

    # Manejar cierre con la X del sistema
    root.protocol("WM_DELETE_WINDOW", root.destroy)

    # Iniciar el loop principal de eventos de Tkinter
    root.mainloop()


if __name__ == "__main__":
    main()