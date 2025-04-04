"""
Módulo para la integración con WhatsApp (vía Twilio).
Proporciona funciones para conectar el bot con la API de WhatsApp de Twilio.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Añadir el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent.parent))

# Importar módulos de Flask y Twilio
from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from src.bot.env_manager import EnvManager
from src.bot.command_processor import CommandProcessor
from src.openai.query_processor import QueryProcessor

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

class WhatsAppBot:
    """Gestiona la integración con WhatsApp vía Twilio."""
    
    def __init__(self, account_sid: Optional[str] = None, auth_token: Optional[str] = None, phone_number: Optional[str] = None):
        """
        Inicializa el bot de WhatsApp.
        
        Args:
            account_sid (str, optional): SID de la cuenta de Twilio.
            auth_token (str, optional): Token de autenticación de Twilio.
            phone_number (str, optional): Número de teléfono de WhatsApp.
                                        Si no se proporcionan, se intentan obtener de las variables de entorno.
        """
        # Cargar credenciales
        if account_sid is None or auth_token is None or phone_number is None:
            env_manager = EnvManager()
            twilio_credentials = env_manager.get_twilio_credentials()
            
            account_sid = account_sid or twilio_credentials['account_sid']
            auth_token = auth_token or twilio_credentials['auth_token']
            phone_number = phone_number or twilio_credentials['phone_number']
        
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.phone_number = phone_number
        
        # Verificar que se han proporcionado las credenciales
        if not self.account_sid or not self.auth_token or not self.phone_number:
            logger.error("No se han proporcionado las credenciales de Twilio")
            raise ValueError("Se requieren las credenciales de Twilio")
        
        # Inicializar cliente de Twilio
        self.client = Client(self.account_sid, self.auth_token)
        
        # Inicializar procesadores
        self.command_processor = CommandProcessor()
        
        # Inicializar aplicación Flask
        self.app = Flask(__name__)
        self.app.route("/whatsapp", methods=["POST"])(self._handle_webhook)
        
        logger.info("WhatsAppBot inicializado correctamente")
    
    def _handle_webhook(self):
        """Maneja las solicitudes entrantes del webhook de Twilio."""
        try:
            # Obtener datos de la solicitud
            incoming_msg = request.values.get('Body', '').strip()
            sender = request.values.get('From', '').replace('whatsapp:', '')
            
            # Crear respuesta
            response = MessagingResponse()
            
            # Procesar el mensaje
            if incoming_msg.startswith('/'):
                # Es un comando
                reply = self.command_processor.process_message(incoming_msg, sender, "whatsapp")
            else:
                # Es una consulta
                try:
                    # Inicializar el procesador de consultas con la clave de API de OpenAI
                    env_manager = EnvManager()
                    api_key = env_manager.get_openai_api_key()
                    
                    if not api_key:
                        reply = "No se ha configurado la clave de API de OpenAI. Por favor, configúrala primero."
                    else:
                        query_processor = QueryProcessor(api_key)
                        reply = query_processor.process_query(incoming_msg)
                
                except Exception as e:
                    logger.error(f"Error al procesar consulta: {e}")
                    reply = "Lo siento, ocurrió un error al procesar tu consulta. Por favor, inténtalo de nuevo."
            
            # Añadir respuesta
            response.message(reply)
            
            return Response(str(response), mimetype="application/xml")
        
        except Exception as e:
            logger.error(f"Error en webhook: {e}")
            return Response("Error", status=500)
    
    def send_message(self, to: str, message: str) -> bool:
        """
        Envía un mensaje de WhatsApp.
        
        Args:
            to (str): Número de teléfono del destinatario.
            message (str): Mensaje a enviar.
            
        Returns:
            bool: True si el mensaje se envió correctamente, False en caso contrario.
        """
        try:
            # Asegurarse de que el número tiene el formato correcto
            if not to.startswith('whatsapp:'):
                to = f'whatsapp:{to}'
            
            # Enviar mensaje
            self.client.messages.create(
                from_=f'whatsapp:{self.phone_number}',
                body=message,
                to=to
            )
            
            logger.info(f"Mensaje enviado a {to}")
            return True
        
        except Exception as e:
            logger.error(f"Error al enviar mensaje: {e}")
            return False
    
    def start(self, host: str = '0.0.0.0', port: int = 5000):
        """
        Inicia el servidor Flask para recibir webhooks.
        
        Args:
            host (str, optional): Host en el que escuchar. Por defecto, '0.0.0.0'.
            port (int, optional): Puerto en el que escuchar. Por defecto, 5000.
        """
        try:
            logger.info(f"Iniciando servidor Flask en {host}:{port}...")
            self.app.run(host=host, port=port)
        except Exception as e:
            logger.error(f"Error al iniciar servidor Flask: {e}")
            raise
    
    def stop(self):
        """Detiene el servidor Flask."""
        # Flask no proporciona un método para detener el servidor desde el código
        # Se debe detener el proceso manualmente
        logger.info("Para detener el servidor Flask, presiona Ctrl+C")
