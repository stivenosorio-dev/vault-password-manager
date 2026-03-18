# vault - Password manager

Manejador de contraseñas local con encriptación de grado profesional.
Desarrollado en Python con interfaz gráfica Tkinter.

## ¿Por qué este proyecto?

Como parte de mi plan de formación como Backend Developer, construí esta
herramienta para practicar criptografía aplicada, arquitectura de clases
y distribución de software portable en Python.

## Características

- Encriptación AES-128-CBC (Fernet) con clave derivada via PBKDF2-HMAC-SHA256
- Contraseña maestra con 480.000 iteraciones de hasheo (estándar NIST 2023)
- Archivo `.vault` portable — respaldable en Google Drive
- CRUD completo de entradas (crear, ver, editar, eliminar)
- Búsqueda en tiempo real
- Generador de contraseñas criptográficamente seguro
- Interfaz oscura con Tkinter

## Tecnologías

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![Tkinter](https://img.shields.io/badge/UI-Tkinter-lightgrey)
![Cryptography](https://img.shields.io/badge/Crypto-Fernet%20%7C%20PBKDF2-green)

## Instalación
```bash
# Clonar el repositorio
git clone https://github.com/stiven-osorio-dev/vault-password-manager.git
cd vault-password-manager

# Instalar dependencia
pip install cryptography

# Ejecutar
python main.py
```

## Arquitectura (preparada para modularización)
```
main.py
├── CryptoManager   → cifrado/descifrado (futuro: crypto/manager.py)
├── VaultStorage    → persistencia en disco (futuro: storage/vault_storage.py)
└── VaultApp        → interfaz gráfica (futuro: ui/)
    ├── Pantalla de desbloqueo
    ├── Pantalla principal
    ├── Diálogo nueva/editar entrada
    └── Diálogo ver entrada
```

## Autor

**Jorge Stiven Osorio** — Backend Developer en formación
[LinkedIn](https://linkedin.com/in/stiven-osorio-dev) ·
[GitHub](https://github.com/stiven-osorio-dev)