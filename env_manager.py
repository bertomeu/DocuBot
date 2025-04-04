"""
Módulo para gestionar las variables de entorno de DocuBot.
Proporciona funciones para cargar y acceder a las variables de entorno.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Añadir el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent.parent))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(Path(__file__).parent.parent.parent, 'logs', 'docubot.log'), 'a')
    ]
)
logger = logging.getLogger(__name__)

class EnvManager:
    """Gestiona las variables de entorno para DocuBot."""
    
    def __init__(self, env_path: Optional[str] = None):
        """
        Inicializa el gestor de variables de entorno.
        
        Args:
            env_path (str, optional): Ruta al archivo .env.
                                     Si no se proporciona, se busca en la raíz del proyecto.
        """
        if env_path is None:
            base_dir = Path(__file__).parent.parent.parent
            env_path = os.path.join(base_dir, '.env')
        
        self.env_path = env_path
        self.env_example_path = os.path.join(Path(__file__).parent.parent.parent, '.env.example')
        
        # Cargar variables de entorno
        self._load_env()
    
    def _load_env(self) -> bool:
        """
        Carga las variables de entorno desde el archivo .env.
        
        Returns:
            bool: True si se cargaron correctamente, False en caso contrario.
        """
        try:
            # Verificar si existe el archivo .env
            if not os.path.isfile(self.env_path):
                logger.warning(f"No se encontró el archivo .env en {self.env_path}")
                
                # Verificar si existe el archivo .env.example
                if os.path.isfile(self.env_example_path):
                    logger.info(f"Se encontró el archivo .env.example en {self.env_example_path}")
                    logger.info("Por favor, crea un archivo .env basado en .env.example con tus propias claves")
                
                return False
            
            # Cargar variables de entorno
            load_dotenv(self.env_path)
            logger.info(f"Variables de entorno cargadas desde {self.env_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error al cargar las variables de entorno: {e}")
            return False
    
    def get_env(self, key: str, default: Any = None) -> Any:
        """
        Obtiene el valor de una variable de entorno.
        
        Args:
            key (str): Nombre de la variable de entorno.
            default (Any, optional): Valor predeterminado si la variable no existe.
            
        Returns:
            Any: Valor de la variable de entorno, o el valor predeterminado si no existe.
        """
        return os.environ.get(key, default)
    
    def get_openai_api_key(self) -> Optional[str]:
        """
        Obtiene la clave de API de OpenAI.
        
        Returns:
            str or None: Clave de API de OpenAI, o None si no está configurada.
        """
        return self.get_env('OPENAI_API_KEY')
    
    def get_telegram_token(self) -> Optional[str]:
        """
        Obtiene el token del bot de Telegram.
        
        Returns:
            str or None: Token del bot de Telegram, o None si no está configurado.
        """
        return self.get_env('TELEGRAM_BOT_TOKEN')
    
    def get_twilio_credentials(self) -> Dict[str, Optional[str]]:
        """
        Obtiene las credenciales de Twilio para WhatsApp.
        
        Returns:
            dict: Credenciales de Twilio.
        """
        return {
            'account_sid': self.get_env('TWILIO_ACCOUNT_SID'),
            'auth_token': self.get_env('TWILIO_AUTH_TOKEN'),
            'phone_number': self.get_env('TWILIO_PHONE_NUMBER')
        }
    
    def get_bot_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración general del bot desde las variables de entorno.
        
        Returns:
            dict: Configuración general del bot.
        """
        return {
            'name': self.get_env('BOT_NAME', 'DocuBot'),
            'platform': self.get_env('BOT_PLATFORM', 'both')
        }
    
    def create_env_file(self) -> bool:
        """
        Crea un archivo .env basado en .env.example si no existe.
        
        Returns:
            bool: True si se creó correctamente, False en caso contrario.
        """
        try:
            # Verificar si ya existe el archivo .env
            if os.path.isfile(self.env_path):
                logger.info(f"El archivo .env ya existe en {self.env_path}")
                return True
            
            # Verificar si existe el archivo .env.example
            if not os.path.isfile(self.env_example_path):
                logger.error(f"No se encontró el archivo .env.example en {self.env_example_path}")
                return False
            
            # Copiar .env.example a .env
            with open(self.env_example_path, 'r', encoding='utf-8') as example_file:
                example_content = example_file.read()
            
            with open(self.env_path, 'w', encoding='utf-8') as env_file:
                env_file.write(example_content)
            
            logger.info(f"Archivo .env creado en {self.env_path} basado en .env.example")
            return True
        
        except Exception as e:
            logger.error(f"Error al crear el archivo .env: {e}")
            return False
