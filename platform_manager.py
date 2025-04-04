"""
Módulo para seleccionar y gestionar las plataformas de mensajería.
Proporciona una interfaz unificada para interactuar con diferentes plataformas.
"""

import os
import sys
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Añadir el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent.parent))

from src.bot.env_manager import EnvManager
from src.platforms.telegram_bot import TelegramBot
from src.platforms.whatsapp_bot import WhatsAppBot

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

class PlatformManager:
    """Gestiona las plataformas de mensajería disponibles."""
    
    def __init__(self):
        """Inicializa el gestor de plataformas."""
        self.env_manager = EnvManager()
        self.telegram_bot = None
        self.whatsapp_bot = None
        self.active_platforms = []
        self.threads = {}
        
        logger.info("PlatformManager inicializado correctamente")
    
    def start_platform(self, platform: str) -> bool:
        """
        Inicia una plataforma específica.
        
        Args:
            platform (str): Plataforma a iniciar ('telegram', 'whatsapp').
            
        Returns:
            bool: True si la plataforma se inició correctamente, False en caso contrario.
        """
        try:
            if platform == 'telegram':
                return self._start_telegram()
            elif platform == 'whatsapp':
                return self._start_whatsapp()
            else:
                logger.error(f"Plataforma desconocida: {platform}")
                return False
        
        except Exception as e:
            logger.error(f"Error al iniciar plataforma {platform}: {e}")
            return False
    
    def _start_telegram(self) -> bool:
        """
        Inicia el bot de Telegram.
        
        Returns:
            bool: True si el bot se inició correctamente, False en caso contrario.
        """
        try:
            # Verificar si ya está activo
            if 'telegram' in self.active_platforms:
                logger.info("El bot de Telegram ya está activo")
                return True
            
            # Obtener token
            token = self.env_manager.get_telegram_token()
            if not token:
                logger.error("No se ha configurado el token de Telegram")
                return False
            
            # Inicializar bot
            self.telegram_bot = TelegramBot(token)
            
            # Iniciar bot en un hilo separado
            telegram_thread = threading.Thread(target=self.telegram_bot.start)
            telegram_thread.daemon = True
            telegram_thread.start()
            
            # Guardar referencia al hilo
            self.threads['telegram'] = telegram_thread
            
            # Marcar como activo
            self.active_platforms.append('telegram')
            
            logger.info("Bot de Telegram iniciado correctamente")
            return True
        
        except Exception as e:
            logger.error(f"Error al iniciar bot de Telegram: {e}")
            return False
    
    def _start_whatsapp(self) -> bool:
        """
        Inicia el bot de WhatsApp.
        
        Returns:
            bool: True si el bot se inició correctamente, False en caso contrario.
        """
        try:
            # Verificar si ya está activo
            if 'whatsapp' in self.active_platforms:
                logger.info("El bot de WhatsApp ya está activo")
                return True
            
            # Obtener credenciales
            twilio_credentials = self.env_manager.get_twilio_credentials()
            if not twilio_credentials['account_sid'] or not twilio_credentials['auth_token'] or not twilio_credentials['phone_number']:
                logger.error("No se han configurado las credenciales de Twilio")
                return False
            
            # Inicializar bot
            self.whatsapp_bot = WhatsAppBot(
                twilio_credentials['account_sid'],
                twilio_credentials['auth_token'],
                twilio_credentials['phone_number']
            )
            
            # Iniciar bot en un hilo separado
            whatsapp_thread = threading.Thread(target=self.whatsapp_bot.start)
            whatsapp_thread.daemon = True
            whatsapp_thread.start()
            
            # Guardar referencia al hilo
            self.threads['whatsapp'] = whatsapp_thread
            
            # Marcar como activo
            self.active_platforms.append('whatsapp')
            
            logger.info("Bot de WhatsApp iniciado correctamente")
            return True
        
        except Exception as e:
            logger.error(f"Error al iniciar bot de WhatsApp: {e}")
            return False
    
    def stop_platform(self, platform: str) -> bool:
        """
        Detiene una plataforma específica.
        
        Args:
            platform (str): Plataforma a detener ('telegram', 'whatsapp').
            
        Returns:
            bool: True si la plataforma se detuvo correctamente, False en caso contrario.
        """
        try:
            if platform == 'telegram':
                return self._stop_telegram()
            elif platform == 'whatsapp':
                return self._stop_whatsapp()
            else:
                logger.error(f"Plataforma desconocida: {platform}")
                return False
        
        except Exception as e:
            logger.error(f"Error al detener plataforma {platform}: {e}")
            return False
    
    def _stop_telegram(self) -> bool:
        """
        Detiene el bot de Telegram.
        
        Returns:
            bool: True si el bot se detuvo correctamente, False en caso contrario.
        """
        try:
            # Verificar si está activo
            if 'telegram' not in self.active_platforms:
                logger.info("El bot de Telegram no está activo")
                return True
            
            # Detener bot
            if self.telegram_bot:
                self.telegram_bot.stop()
            
            # Eliminar de la lista de activos
            self.active_platforms.remove('telegram')
            
            logger.info("Bot de Telegram detenido correctamente")
            return True
        
        except Exception as e:
            logger.error(f"Error al detener bot de Telegram: {e}")
            return False
    
    def _stop_whatsapp(self) -> bool:
        """
        Detiene el bot de WhatsApp.
        
        Returns:
            bool: True si el bot se detuvo correctamente, False en caso contrario.
        """
        try:
            # Verificar si está activo
            if 'whatsapp' not in self.active_platforms:
                logger.info("El bot de WhatsApp no está activo")
                return True
            
            # Detener bot
            if self.whatsapp_bot:
                self.whatsapp_bot.stop()
            
            # Eliminar de la lista de activos
            self.active_platforms.remove('whatsapp')
            
            logger.info("Bot de WhatsApp detenido correctamente")
            return True
        
        except Exception as e:
            logger.error(f"Error al detener bot de WhatsApp: {e}")
            return False
    
    def start_all_platforms(self) -> bool:
        """
        Inicia todas las plataformas configuradas.
        
        Returns:
            bool: True si todas las plataformas se iniciaron correctamente, False en caso contrario.
        """
        try:
            # Obtener plataforma configurada
            platform = self.env_manager.get_bot_config()['platform']
            
            if platform == 'both':
                # Iniciar ambas plataformas
                telegram_success = self.start_platform('telegram')
                whatsapp_success = self.start_platform('whatsapp')
                
                return telegram_success and whatsapp_success
            
            elif platform == 'telegram':
                # Iniciar solo Telegram
                return self.start_platform('telegram')
            
            elif platform == 'whatsapp':
                # Iniciar solo WhatsApp
                return self.start_platform('whatsapp')
            
            else:
                logger.error(f"Plataforma desconocida: {platform}")
                return False
        
        except Exception as e:
            logger.error(f"Error al iniciar todas las plataformas: {e}")
            return False
    
    def stop_all_platforms(self) -> bool:
        """
        Detiene todas las plataformas activas.
        
        Returns:
            bool: True si todas las plataformas se detuvieron correctamente, False en caso contrario.
        """
        try:
            success = True
            
            # Detener todas las plataformas activas
            for platform in list(self.active_platforms):  # Crear una copia para evitar problemas al modificar durante la iteración
                if not self.stop_platform(platform):
                    success = False
            
            return success
        
        except Exception as e:
            logger.error(f"Error al detener todas las plataformas: {e}")
            return False
    
    def get_active_platforms(self) -> List[str]:
        """
        Obtiene las plataformas activas.
        
        Returns:
            list: Lista de plataformas activas.
        """
        return self.active_platforms
