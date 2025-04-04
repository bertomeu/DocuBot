"""
Módulo principal del bot DocuBot.
Define la estructura base y la lógica principal del bot.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Añadir el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent.parent))

from src.database.schema import DatabaseManager
from src.database.document_manager import DocumentManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(Path(__file__).parent.parent, 'logs', 'docubot.log'), 'a')
    ]
)
logger = logging.getLogger(__name__)

class DocuBot:
    """Clase principal del bot DocuBot."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa el bot DocuBot.
        
        Args:
            config_path (str, optional): Ruta al archivo de configuración.
                                        Si no se proporciona, se usa la configuración de la base de datos.
        """
        # Definir rutas
        self.base_dir = Path(__file__).parent.parent
        self.db_path = os.path.join(self.base_dir, 'data', 'docubot.db')
        self.documents_dir = os.path.join(self.base_dir, 'data', 'documents')
        
        # Crear directorios necesarios
        os.makedirs(os.path.join(self.base_dir, 'logs'), exist_ok=True)
        os.makedirs(self.documents_dir, exist_ok=True)
        
        # Inicializar gestores
        self.db_manager = DatabaseManager(self.db_path)
        self.document_manager = DocumentManager(self.db_path)
        
        # Cargar configuración
        self.config = self._load_config(config_path)
        
        # Estado del bot
        self.is_running = False
        self.platform = None
        self.openai_api_key = None
        
        logger.info("DocuBot inicializado")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Carga la configuración del bot.
        
        Args:
            config_path (str, optional): Ruta al archivo de configuración.
            
        Returns:
            dict: Configuración del bot.
        """
        config = {
            'name': 'DocuBot',
            'description': 'Asistente de documentación basado en IA',
            'instructions': 'Responde preguntas basadas en la documentación proporcionada.',
            'platform': 'both',
            'openai_api_key': None
        }
        
        try:
            # Conectar a la base de datos
            if not self.db_manager.connect():
                logger.error("No se pudo conectar a la base de datos para cargar la configuración")
                return config
            
            # Obtener configuración de la base de datos
            self.db_manager.cursor.execute("SELECT * FROM bot_config LIMIT 1")
            db_config = self.db_manager.cursor.fetchone()
            
            # Desconectar de la base de datos
            self.db_manager.disconnect()
            
            if db_config:
                config['name'] = db_config['name']
                config['description'] = db_config['description']
                config['instructions'] = db_config['instructions']
                config['platform'] = db_config['platform']
                config['openai_api_key'] = db_config['openai_api_key']
                
                logger.info("Configuración cargada desde la base de datos")
            else:
                logger.warning("No se encontró configuración en la base de datos, usando valores predeterminados")
        
        except Exception as e:
            logger.error(f"Error al cargar la configuración: {e}")
        
        return config
    
    def update_config(self, name: Optional[str] = None, description: Optional[str] = None, 
                     instructions: Optional[str] = None, platform: Optional[str] = None,
                     openai_api_key: Optional[str] = None) -> bool:
        """
        Actualiza la configuración del bot.
        
        Args:
            name (str, optional): Nuevo nombre del bot.
            description (str, optional): Nueva descripción del bot.
            instructions (str, optional): Nuevas instrucciones para el bot.
            platform (str, optional): Nueva plataforma ('whatsapp', 'telegram', 'both').
            openai_api_key (str, optional): Nueva clave de API de OpenAI.
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario.
        """
        try:
            # Verificar que se proporcionó al menos un campo para actualizar
            if all(param is None for param in [name, description, instructions, platform, openai_api_key]):
                logger.warning("No se proporcionó ningún campo para actualizar")
                return False
            
            # Conectar a la base de datos
            if not self.db_manager.connect():
                logger.error("No se pudo conectar a la base de datos para actualizar la configuración")
                return False
            
            # Construir la consulta de actualización
            update_fields = []
            params = []
            
            if name is not None:
                update_fields.append("name = ?")
                params.append(name)
                self.config['name'] = name
            
            if description is not None:
                update_fields.append("description = ?")
                params.append(description)
                self.config['description'] = description
            
            if instructions is not None:
                update_fields.append("instructions = ?")
                params.append(instructions)
                self.config['instructions'] = instructions
            
            if platform is not None:
                if platform not in ['whatsapp', 'telegram', 'both']:
                    logger.error(f"Plataforma no válida: {platform}")
                    self.db_manager.disconnect()
                    return False
                
                update_fields.append("platform = ?")
                params.append(platform)
                self.config['platform'] = platform
            
            if openai_api_key is not None:
                update_fields.append("openai_api_key = ?")
                params.append(openai_api_key)
                self.config['openai_api_key'] = openai_api_key
            
            # Añadir la fecha de actualización
            update_fields.append("updated_at = ?")
            params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # Ejecutar la consulta
            self.db_manager.cursor.execute(
                f"UPDATE bot_config SET {', '.join(update_fields)} WHERE id = 1",
                params
            )
            self.db_manager.connection.commit()
            
            # Desconectar de la base de datos
            self.db_manager.disconnect()
            
            logger.info("Configuración actualizada correctamente")
            return True
        
        except Exception as e:
            logger.error(f"Error al actualizar la configuración: {e}")
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
                self.db_manager.disconnect()
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración actual del bot.
        
        Returns:
            dict: Configuración actual del bot.
        """
        return self.config
    
    def start(self, platform: Optional[str] = None) -> bool:
        """
        Inicia el bot en la plataforma especificada.
        
        Args:
            platform (str, optional): Plataforma en la que iniciar el bot ('whatsapp', 'telegram').
                                     Si no se proporciona, se usa la configuración actual.
            
        Returns:
            bool: True si el bot se inició correctamente, False en caso contrario.
        """
        try:
            # Determinar la plataforma
            if platform is None:
                platform = self.config['platform']
            
            # Verificar que la plataforma es válida
            if platform not in ['whatsapp', 'telegram', 'both']:
                logger.error(f"Plataforma no válida: {platform}")
                return False
            
            # Verificar que se ha configurado la clave de API de OpenAI
            if not self.config['openai_api_key']:
                logger.error("No se ha configurado la clave de API de OpenAI")
                return False
            
            # Establecer el estado del bot
            self.is_running = True
            self.platform = platform
            self.openai_api_key = self.config['openai_api_key']
            
            logger.info(f"Bot iniciado en la plataforma: {platform}")
            return True
        
        except Exception as e:
            logger.error(f"Error al iniciar el bot: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Detiene el bot.
        
        Returns:
            bool: True si el bot se detuvo correctamente, False en caso contrario.
        """
        try:
            # Establecer el estado del bot
            self.is_running = False
            
            logger.info("Bot detenido")
            return True
        
        except Exception as e:
            logger.error(f"Error al detener el bot: {e}")
            return False
    
    def is_active(self) -> bool:
        """
        Verifica si el bot está activo.
        
        Returns:
            bool: True si el bot está activo, False en caso contrario.
        """
        return self.is_running
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del bot.
        
        Returns:
            dict: Estado actual del bot.
        """
        return {
            'is_running': self.is_running,
            'platform': self.platform,
            'config': self.config
        }
