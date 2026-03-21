# ══════════════════════════════════════════════════════════════════════════════
# VAULT STORAGE
# ══════════════════════════════════════════════════════════════════════════════
# Responsabilidad: leer y escribir el archivo .vault en disco.
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


import json
import base64
from config.constants import VAULT_FILENAME, VAULT_VERSION
from crypto.manager import CryptoManager
from pathlib import Path


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
