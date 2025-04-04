# DocuBot

DocuBot es un bot inteligente basado en Python que utiliza la API de OpenAI para responder preguntas basadas en documentos PDF. Puede integrarse con WhatsApp, Telegram o ambos, según tus necesidades.



## Características

- 🤖 Bot inteligente que responde preguntas basadas en tus documentos
- 📄 Procesamiento e indexación de documentos PDF
- 🔍 Búsqueda semántica en documentos utilizando embeddings de OpenAI
- 💬 Integración con WhatsApp (vía Twilio) y Telegram
- 🔄 Configuración flexible para personalizar el comportamiento del bot
- 🛡️ Gestión segura de claves API mediante variables de entorno
- 📊 Base de datos SQLite para almacenar documentos y configuraciones

## Requisitos

- Python 3.8 o superior
- Cuenta de OpenAI con API key
- Para WhatsApp: Cuenta de Twilio con WhatsApp Sandbox
- Para Telegram: Bot de Telegram creado con BotFather

## Instalación

### Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/DocuBot.git
cd DocuBot
```

### Crear un entorno virtual

```bash
python -m venv venv
```

### Activar el entorno virtual

En Windows:
```bash
venv\Scripts\activate
```

En macOS/Linux:
```bash
source venv/bin/activate
```

### Instalar dependencias

```bash
pip install -r requirements.txt
```

### Configurar variables de entorno

1. Crea un archivo `.env` en la raíz del proyecto basado en el archivo `.env.example`:

```bash
cp .env.example .env
```

2. Edita el archivo `.env` y añade tus claves API y configuraciones:

```
# API de OpenAI
OPENAI_API_KEY=tu_clave_api_aqui

# Configuración de Telegram
TELEGRAM_BOT_TOKEN=tu_token_de_bot_aqui

# Configuración de WhatsApp (Twilio)
TWILIO_ACCOUNT_SID=tu_account_sid_aqui
TWILIO_AUTH_TOKEN=tu_auth_token_aqui
TWILIO_PHONE_NUMBER=tu_numero_de_whatsapp_aqui

# Configuración general
BOT_NAME=DocuBot
BOT_PLATFORM=both  # Opciones: whatsapp, telegram, both
```

### Inicializar la base de datos

```bash
python src/database/init_db.py
```

## Inicialización del proyecto en VSCode

Para inicializar y trabajar con el proyecto en Visual Studio Code, sigue estos pasos:

1. Abre VSCode
2. Selecciona "File" > "Open Folder" y navega hasta la carpeta del proyecto DocuBot
3. VSCode detectará automáticamente el entorno virtual. Si no lo hace, puedes seleccionarlo manualmente:
   - Presiona `Ctrl+Shift+P` (o `Cmd+Shift+P` en macOS)
   - Escribe "Python: Select Interpreter"
   - Selecciona el intérprete de Python en la carpeta `venv`

4. Configuración recomendada para VSCode:
   - Instala las extensiones: "Python", "Pylance", "SQLite Viewer"
   - Crea un archivo `.vscode/settings.json` con el siguiente contenido:

```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "autopep8",
    "editor.formatOnSave": true,
    "python.analysis.extraPaths": [
        "${workspaceFolder}"
    ]
}
```

5. Para depurar el proyecto:
   - Crea un archivo `.vscode/launch.json` con el siguiente contenido:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Archivo actual",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": true,
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        },
        {
            "name": "Python: Iniciar Bot",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal",
            "justMyCode": true,
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        }
    ]
}
```

## Uso

### Iniciar el bot

```bash
python main.py
```

### Comandos disponibles

- `/start` - Inicia la interacción con el bot
- `/help` - Muestra la ayuda
- `/config` - Configura el bot
- `/upload` - Sube un documento PDF
- `/list` - Lista los documentos disponibles
- `/delete` - Elimina un documento
- `/search` - Busca en los documentos
- `/about` - Muestra información sobre el bot

## Conexión con Telegram

Para conectar DocuBot con Telegram, sigue estos pasos:

1. **Crear un bot en Telegram**:
   - Abre Telegram y busca a [@BotFather](https://t.me/BotFather)
   - Envía el comando `/newbot`
   - Sigue las instrucciones para crear un nuevo bot
   - BotFather te proporcionará un token de API. Guárdalo en tu archivo `.env` como `TELEGRAM_BOT_TOKEN`

2. **Configurar DocuBot para usar Telegram**:
   - Asegúrate de que en tu archivo `.env` tienes configurado:
     ```
     BOT_PLATFORM=telegram
     # o
     BOT_PLATFORM=both
     ```

3. **Iniciar el bot**:
   ```bash
   python main.py
   ```

4. **Interactuar con el bot**:
   - Busca tu bot en Telegram por el nombre que le diste
   - Inicia una conversación con el comando `/start`
   - Ahora puedes enviar mensajes y documentos PDF a tu bot

## Conexión con WhatsApp

Para conectar DocuBot con WhatsApp (a través de Twilio), sigue estos pasos:

1. **Crear una cuenta en Twilio**:
   - Regístrate en [Twilio](https://www.twilio.com/)
   - Activa el [Sandbox de WhatsApp](https://www.twilio.com/console/sms/whatsapp/learn)
   - Obtén tu Account SID y Auth Token desde el [Dashboard de Twilio](https://www.twilio.com/console)
   - Guarda estos datos en tu archivo `.env`:
     ```
     TWILIO_ACCOUNT_SID=tu_account_sid_aqui
     TWILIO_AUTH_TOKEN=tu_auth_token_aqui
     TWILIO_PHONE_NUMBER=tu_numero_de_whatsapp_aqui
     ```

2. **Configurar un webhook para Twilio**:
   - DocuBot necesita ser accesible desde Internet para recibir mensajes de WhatsApp
   - Puedes usar [ngrok](https://ngrok.com/) para exponer tu servidor local:
     ```bash
     ngrok http 5000
     ```
   - Copia la URL HTTPS generada por ngrok (por ejemplo, `https://abcd1234.ngrok.io`)
   - En la [consola de Twilio](https://www.twilio.com/console/sms/whatsapp/sandbox), configura el webhook:
     - En "When a message comes in", ingresa: `https://abcd1234.ngrok.io/whatsapp`

3. **Configurar DocuBot para usar WhatsApp**:
   - Asegúrate de que en tu archivo `.env` tienes configurado:
     ```
     BOT_PLATFORM=whatsapp
     # o
     BOT_PLATFORM=both
     ```

4. **Iniciar el bot**:
   ```bash
   python main.py
   ```

5. **Conectar tu WhatsApp al Sandbox**:
   - Sigue las instrucciones en la [consola de Twilio](https://www.twilio.com/console/sms/whatsapp/sandbox)
   - Normalmente, deberás enviar un código específico al número de WhatsApp de Twilio
   - Una vez conectado, podrás enviar mensajes a tu bot

## Estructura del Proyecto

```
DocuBot/
├── config/                 # Archivos de configuración
├── data/                   # Datos y base de datos
│   ├── documents/          # Documentos procesados
│   └── vector_store/       # Índices vectoriales para búsqueda
├── docs/                   # Documentación
│   └── images/             # Imágenes para documentación
├── logs/                   # Archivos de registro
├── src/                    # Código fuente
│   ├── bot/                # Núcleo del bot
│   │   ├── bot.py          # Clase principal del bot
│   │   ├── command_processor.py  # Procesador de comandos
│   │   ├── config_manager.py     # Gestor de configuración
│   │   └── env_manager.py        # Gestor de variables de entorno
│   ├── database/           # Gestión de base de datos
│   │   ├── document_manager.py   # Gestor de documentos
│   │   ├── init_db.py            # Script de inicialización
│   │   └── schema.py             # Esquema de la base de datos
│   ├── openai/             # Integración con OpenAI
│   │   ├── document_processor.py # Procesador de documentos
│   │   ├── openai_manager.py     # Gestor de OpenAI
│   │   └── query_processor.py    # Procesador de consultas
│   └── platforms/          # Integración con plataformas
│       ├── platform_manager.py   # Gestor de plataformas
│       ├── telegram_bot.py       # Bot de Telegram
│       └── whatsapp_bot.py       # Bot de WhatsApp
├── temp/                   # Archivos temporales
├── .env                    # Variables de entorno (no incluido en Git)
├── .env.example            # Ejemplo de variables de entorno
├── .gitignore              # Archivos ignorados por Git
├── LICENSE                 # Licencia del proyecto
├── main.py                 # Punto de entrada principal
├── README.md               # Este archivo
└── requirements.txt        # Dependencias del proyecto
```



## Contribuir

Las contribuciones son bienvenidas. Por favor, siente libre de abrir un issue o enviar un pull request.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Si tienes alguna pregunta o sugerencia, no dudes en contactarme.

---

Desarrollado con ❤️ usando Python, SQLite y OpenAI.
