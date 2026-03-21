# ══════════════════════════════════════════════════════════════════════════════
# CRYPTO MANAGER
# ══════════════════════════════════════════════════════════════════════════════
# Responsabilidad: todo lo relacionado con encriptación y hash.
#
# Algoritmo usado:
#   - PBKDF2-HMAC-SHA256: deriva una clave de 32 bytes desde la contraseña maestra
#   - Fernet (AES-128-CBC + HMAC-SHA256): encripta/desencripta los datos del vault
#
# Por qué Fernet:
#   - Incluye autenticación del mensaje (HMAC) — detecta datos corruptos o alterados
#   - Usa IV aleatorio en cada encriptación — mismo texto = diferente cifrado
#   - Estándar de la librería cryptography de Python — auditado y confiable

from config.constants import PBKDF2_ITERATIONS, SALT_SIZE
import sys
import base64



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
