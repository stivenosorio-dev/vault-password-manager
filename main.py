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

import sys
import secrets
import string
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime
from ui.app import VaultApp

from config.constants import COLORS, FONTS, VAULT_FILENAME, PBKDF2_ITERATIONS, SALT_SIZE, VAULT_VERSION
from crypto.manager import CryptoManager
from storage.vault_storage import VaultStorage 


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