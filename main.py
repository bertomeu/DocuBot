"""
Punto de entrada principal para DocuBot.
Inicia el bot y gestiona las plataformas de mensajería.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Añadir el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent))

from src.bot.bot import DocuBot
from src.bot.env_manager import EnvManager
from src.database.schema import DatabaseManager
from src.platforms.platform_manager import PlatformManager

# Configurar logging
os.makedirs(os.path.join(Path(__file__).parent, 'logs'), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(Path(__file__).parent, 'logs', 'docubot.log'), 'a')
    ]
)
logger = logging.getLogger(__name__)

def initialize_database():
    """Inicializa la base de datos si no existe."""
    try:
        # Definir la ruta de la base de datos
        base_dir = Path(__file__).parent
        db_path = os.path.join(base_dir, 'data', 'docubot.db')
        
        # Verificar si la base de datos ya existe
        if os.path.isfile(db_path):
            logger.info(f"La base de datos ya existe en {db_path}")
            return True
        
        # Importar e inicializar la base de datos
        from src.database.init_db import initialize_database as init_db
        success = init_db()
        
        if success:
            logger.info("Base de datos inicializada correctamente")
        else:
            logger.error("Error al inicializar la base de datos")
        
        return success
    
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
        return False

def check_environment():
    """Verifica que el entorno esté correctamente configurado."""
    try:
        # Inicializar gestor de variables de entorno
        env_manager = EnvManager()
        
        # Verificar si existe el archivo .env
        if not os.path.isfile(os.path.join(Path(__file__).parent, '.env')):
            # Crear archivo .env basado en .env.example
            if env_manager.create_env_file():
                logger.info("Archivo .env creado correctamente")
                logger.info("Por favor, edita el archivo .env con tus propias claves y configuraciones")
                return False
            else:
                logger.error("Error al crear el archivo .env")
                return False
        
        # Verificar claves necesarias
        openai_api_key = env_manager.get_openai_api_key()
        if not openai_api_key:
            logger.warning("No se ha configurado la clave de API de OpenAI en el archivo .env")
            logger.info("Por favor, edita el archivo .env y añade tu clave de API de OpenAI")
            return False
        
        # Verificar plataforma configurada
        platform = env_manager.get_bot_config()['platform']
        if platform in ['telegram', 'both']:
            telegram_token = env_manager.get_telegram_token()
            if not telegram_token:
                logger.warning("No se ha configurado el token de Telegram en el archivo .env")
                logger.info("Por favor, edita el archivo .env y añade tu token de Telegram")
                return False
        
        if platform in ['whatsapp', 'both']:
            twilio_credentials = env_manager.get_twilio_credentials()
            if not twilio_credentials['account_sid'] or not twilio_credentials['auth_token'] or not twilio_credentials['phone_number']:
                logger.warning("No se han configurado las credenciales de Twilio en el archivo .env")
                logger.info("Por favor, edita el archivo .env y añade tus credenciales de Twilio")
                return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error al verificar el entorno: {e}")
        return False

def main():
    """Función principal para iniciar DocuBot."""
    try:
        # Parsear argumentos de línea de comandos
        parser = argparse.ArgumentParser(description='DocuBot - Bot de documentación basado en IA')
        parser.add_argument('--platform', choices=['telegram', 'whatsapp', 'both'], help='Plataforma a utilizar')
        parser.add_argument('--init-only', action='store_true', help='Solo inicializar la base de datos y salir')
        args = parser.parse_args()
        
        # Mostrar banner
        print("""
        ╔═══════════════════════════════════════════════╗
        ║                                               ║
        ║   ██████╗  ██████╗  ██████╗██╗   ██╗██████╗   ║
        ║   ██╔══██╗██╔═══██╗██╔════╝██║   ██║██╔══██╗  ║
        ║   ██║  ██║██║   ██║██║     ██║   ██║██████╔╝  ║
        ║   ██║  ██║██║   ██║██║     ██║   ██║██╔══██╗  ║
        ║   ██████╔╝╚██████╔╝╚██████╗╚██████╔╝██████╔╝  ║
        ║   ╚═════╝  ╚═════╝  ╚═════╝ ╚═════╝ ╚═════╝   ║
        ║                                               ║
        ║   Bot de documentación basado en IA           ║
        ║                                               ║
        ╚═══════════════════════════════════════════════╝
        """)
        
        # Inicializar la base de datos
        if not initialize_database():
            logger.error("No se pudo inicializar la base de datos. Saliendo...")
            return 1
        
        # Si solo se pidió inicializar, salir
        if args.init_only:
            logger.info("Inicialización completada. Saliendo...")
            return 0
        
        # Verificar el entorno
        if not check_environment():
            logger.error("El entorno no está correctamente configurado. Saliendo...")
            return 1
        
        # Inicializar el bot
        docubot = DocuBot()
        
        # Inicializar el gestor de plataformas
        platform_manager = PlatformManager()
        
        # Determinar la plataforma a utilizar
        platform = args.platform or docubot.config['platform']
        
        # Iniciar las plataformas
        if platform == 'both':
            logger.info("Iniciando DocuBot en ambas plataformas (Telegram y WhatsApp)...")
            platform_manager.start_all_platforms()
        elif platform == 'telegram':
            logger.info("Iniciando DocuBot en Telegram...")
            platform_manager.start_platform('telegram')
        elif platform == 'whatsapp':
            logger.info("Iniciando DocuBot en WhatsApp...")
            platform_manager.start_platform('whatsapp')
        else:
            logger.error(f"Plataforma desconocida: {platform}")
            return 1
        
        # Mantener el programa en ejecución
        logger.info("DocuBot iniciado correctamente. Presiona Ctrl+C para detener.")
        try:
            # Esperar indefinidamente
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Deteniendo DocuBot...")
            platform_manager.stop_all_platforms()
            logger.info("DocuBot detenido correctamente.")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error en la función principal: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
