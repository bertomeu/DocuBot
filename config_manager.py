"""
Módulo para la configuración del bot DocuBot.
Proporciona una interfaz para gestionar la configuración del bot.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Añadir el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent.parent))

from src.database.schema import DatabaseManager

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

class ConfigManager:
    """Gestiona la configuración del bot DocuBot."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa el gestor de configuración.
        
        Args:
            db_path (str, optional): Ruta al archivo de base de datos SQLite.
                                    Si no se proporciona, se usa la ruta predeterminada.
        """
        if db_path is None:
            base_dir = Path(__file__).parent.parent.parent
            db_path = os.path.join(base_dir, 'data', 'docubot.db')
        
        self.db_path = db_path
        self.db_manager = DatabaseManager(db_path)
        
        # Crear directorio de configuración si no existe
        config_dir = os.path.join(Path(__file__).parent.parent.parent, 'config')
        os.makedirs(config_dir, exist_ok=True)
        
        # Ruta al archivo de configuración local
        self.config_file = os.path.join(config_dir, 'settings.json')
    
    def load_config(self) -> Dict[str, Any]:
        """
        Carga la configuración del bot desde la base de datos.
        
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
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Guarda la configuración del bot en la base de datos.
        
        Args:
            config (dict): Configuración del bot.
            
        Returns:
            bool: True si la operación fue exitosa, False en caso contrario.
        """
        try:
            # Conectar a la base de datos
            if not self.db_manager.connect():
                logger.error("No se pudo conectar a la base de datos para guardar la configuración")
                return False
            
            # Verificar si ya existe una configuración
            self.db_manager.cursor.execute("SELECT COUNT(*) FROM bot_config")
            count = self.db_manager.cursor.fetchone()[0]
            
            if count == 0:
                # Insertar nueva configuración
                self.db_manager.cursor.execute('''
                INSERT INTO bot_config (name, description, instructions, platform, openai_api_key)
                VALUES (?, ?, ?, ?, ?)
                ''', (
                    config.get('name', 'DocuBot'),
                    config.get('description', 'Asistente de documentación basado en IA'),
                    config.get('instructions', 'Responde preguntas basadas en la documentación proporcionada.'),
                    config.get('platform', 'both'),
                    config.get('openai_api_key')
                ))
            else:
                # Actualizar configuración existente
                self.db_manager.cursor.execute('''
                UPDATE bot_config SET
                    name = ?,
                    description = ?,
                    instructions = ?,
                    platform = ?,
                    openai_api_key = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
                ''', (
                    config.get('name', 'DocuBot'),
                    config.get('description', 'Asistente de documentación basado en IA'),
                    config.get('instructions', 'Responde preguntas basadas en la documentación proporcionada.'),
                    config.get('platform', 'both'),
                    config.get('openai_api_key')
                ))
            
            self.db_manager.connection.commit()
            
            # Desconectar de la base de datos
            self.db_manager.disconnect()
            
            # Guardar también en archivo local para respaldo
            self._save_to_file(config)
            
            logger.info("Configuración guardada correctamente")
            return True
        
        except Exception as e:
            logger.error(f"Error al guardar la configuración: {e}")
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
                self.db_manager.disconnect()
            return False
    
    def _save_to_file(self, config: Dict[str, Any]) -> bool:
        """
        Guarda la configuración en un archivo local.
        
        Args:
            config (dict): Configuración del bot.
            
        Returns:
            bool: True si la operación fue exitosa, False en caso contrario.
        """
        try:
            # Crear una copia de la configuración sin la clave de API
            safe_config = config.copy()
            safe_config['openai_api_key'] = '***HIDDEN***' if config.get('openai_api_key') else None
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(safe_config, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Configuración guardada en archivo: {self.config_file}")
            return True
        
        except Exception as e:
            logger.error(f"Error al guardar la configuración en archivo: {e}")
            return False
    
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
        # Cargar configuración actual
        current_config = self.load_config()
        
        # Actualizar campos proporcionados
        if name is not None:
            current_config['name'] = name
        
        if description is not None:
            current_config['description'] = description
        
        if instructions is not None:
            current_config['instructions'] = instructions
        
        if platform is not None:
            if platform not in ['whatsapp', 'telegram', 'both']:
                logger.error(f"Plataforma no válida: {platform}")
                return False
            current_config['platform'] = platform
        
        if openai_api_key is not None:
            current_config['openai_api_key'] = openai_api_key
        
        # Guardar configuración actualizada
        return self.save_config(current_config)
    
    def get_openai_api_key(self) -> Optional[str]:
        """
        Obtiene la clave de API de OpenAI.
        
        Returns:
            str or None: Clave de API de OpenAI, o None si no está configurada.
        """
        config = self.load_config()
        return config.get('openai_api_key')
    
    def set_openai_api_key(self, api_key: str) -> bool:
        """
        Establece la clave de API de OpenAI.
        
        Args:
            api_key (str): Clave de API de OpenAI.
            
        Returns:
            bool: True si la operación fue exitosa, False en caso contrario.
        """
        return self.update_config(openai_api_key=api_key)
    
    def get_platform(self) -> str:
        """
        Obtiene la plataforma configurada.
        
        Returns:
            str: Plataforma configurada ('whatsapp', 'telegram', 'both').
        """
        config = self.load_config()
        return config.get('platform', 'both')
    
    def set_platform(self, platform: str) -> bool:
        """
        Establece la plataforma.
        
        Args:
            platform (str): Plataforma ('whatsapp', 'telegram', 'both').
            
        Returns:
            bool: True si la operación fue exitosa, False en caso contrario.
        """
        if platform not in ['whatsapp', 'telegram', 'both']:
            logger.error(f"Plataforma no válida: {platform}")
            return False
        
        return self.update_config(platform=platform)
