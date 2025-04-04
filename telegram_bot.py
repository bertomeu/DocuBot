"""
Módulo para la integración con Telegram.
Proporciona funciones para conectar el bot con la API de Telegram.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Callable

# Añadir el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent.parent))

# Importar módulos de Telegram
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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

class TelegramBot:
    """Gestiona la integración con Telegram."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Inicializa el bot de Telegram.
        
        Args:
            token (str, optional): Token del bot de Telegram.
                                  Si no se proporciona, se intenta obtener de las variables de entorno.
        """
        # Cargar el token
        if token is None:
            env_manager = EnvManager()
            token = env_manager.get_telegram_token()
        
        self.token = token
        
        # Verificar que se ha proporcionado un token
        if not self.token:
            logger.error("No se ha proporcionado un token de Telegram")
            raise ValueError("Se requiere un token de Telegram")
        
        # Inicializar procesadores
        self.command_processor = CommandProcessor()
        
        # Inicializar la aplicación de Telegram
        self.application = Application.builder().token(self.token).build()
        
        # Registrar manejadores
        self._register_handlers()
        
        logger.info("TelegramBot inicializado correctamente")
    
    def _register_handlers(self):
        """Registra los manejadores de comandos y mensajes."""
        # Manejadores de comandos
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self._handle_help))
        self.application.add_handler(CommandHandler("config", self._handle_config))
        self.application.add_handler(CommandHandler("upload", self._handle_upload))
        self.application.add_handler(CommandHandler("list", self._handle_list))
        self.application.add_handler(CommandHandler("delete", self._handle_delete))
        self.application.add_handler(CommandHandler("search", self._handle_search))
        self.application.add_handler(CommandHandler("about", self._handle_about))
        
        # Manejador de mensajes
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        # Manejador de documentos
        self.application.add_handler(MessageHandler(filters.Document.PDF, self._handle_document))
    
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /start."""
        response = self.command_processor.process_message("/start", str(update.effective_user.id), "telegram")
        await update.message.reply_text(response)
    
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /help."""
        response = self.command_processor.process_message("/help", str(update.effective_user.id), "telegram")
        await update.message.reply_text(response)
    
    async def _handle_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /config."""
        response = self.command_processor.process_message("/config", str(update.effective_user.id), "telegram")
        await update.message.reply_text(response)
    
    async def _handle_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /upload."""
        response = self.command_processor.process_message("/upload", str(update.effective_user.id), "telegram")
        await update.message.reply_text(response)
    
    async def _handle_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /list."""
        response = self.command_processor.process_message("/list", str(update.effective_user.id), "telegram")
        await update.message.reply_text(response)
    
    async def _handle_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /delete."""
        args = context.args[0] if context.args else ""
        response = self.command_processor.process_message(f"/delete {args}", str(update.effective_user.id), "telegram")
        await update.message.reply_text(response)
    
    async def _handle_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /search."""
        args = " ".join(context.args) if context.args else ""
        response = self.command_processor.process_message(f"/search {args}", str(update.effective_user.id), "telegram")
        await update.message.reply_text(response)
    
    async def _handle_about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /about."""
        response = self.command_processor.process_message("/about", str(update.effective_user.id), "telegram")
        await update.message.reply_text(response)
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja los mensajes de texto."""
        # Indicar que el bot está escribiendo
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Procesar el mensaje
        try:
            # Inicializar el procesador de consultas con la clave de API de OpenAI
            env_manager = EnvManager()
            api_key = env_manager.get_openai_api_key()
            
            if not api_key:
                await update.message.reply_text("No se ha configurado la clave de API de OpenAI. Por favor, configúrala primero.")
                return
            
            query_processor = QueryProcessor(api_key)
            
            # Procesar la consulta
            response = query_processor.process_query(update.message.text)
            
            # Enviar la respuesta
            await update.message.reply_text(response)
        
        except Exception as e:
            logger.error(f"Error al procesar mensaje: {e}")
            await update.message.reply_text("Lo siento, ocurrió un error al procesar tu mensaje. Por favor, inténtalo de nuevo.")
    
    async def _handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja los documentos PDF."""
        # Verificar que es un PDF
        document = update.message.document
        if not document.mime_type == "application/pdf":
            await update.message.reply_text("Solo se aceptan documentos PDF.")
            return
        
        # Indicar que el bot está procesando el documento
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await update.message.reply_text("Procesando documento... Esto puede tardar unos momentos.")
        
        try:
            # Descargar el documento
            file = await context.bot.get_file(document.file_id)
            
            # Crear directorio temporal si no existe
            temp_dir = os.path.join(Path(__file__).parent.parent.parent, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Guardar el documento
            file_path = os.path.join(temp_dir, document.file_name)
            await file.download_to_drive(file_path)
            
            # Inicializar el procesador de consultas con la clave de API de OpenAI
            env_manager = EnvManager()
            api_key = env_manager.get_openai_api_key()
            
            if not api_key:
                await update.message.reply_text("No se ha configurado la clave de API de OpenAI. Por favor, configúrala primero.")
                return
            
            query_processor = QueryProcessor(api_key)
            
            # Procesar el documento
            document_id = query_processor.upload_and_process_document(
                file_path,
                document.file_name,
                f"Documento subido por {update.effective_user.username or update.effective_user.id} vía Telegram"
            )
            
            if document_id:
                await update.message.reply_text(f"Documento procesado correctamente (ID: {document_id}).")
            else:
                await update.message.reply_text("Error al procesar el documento. Por favor, inténtalo de nuevo.")
            
            # Eliminar el archivo temporal
            os.remove(file_path)
        
        except Exception as e:
            logger.error(f"Error al procesar documento: {e}")
            await update.message.reply_text("Lo siento, ocurrió un error al procesar el documento. Por favor, inténtalo de nuevo.")
    
    def start(self):
        """Inicia el bot de Telegram."""
        try:
            logger.info("Iniciando bot de Telegram...")
            self.application.run_polling()
        except Exception as e:
            logger.error(f"Error al iniciar el bot de Telegram: {e}")
            raise
    
    def stop(self):
        """Detiene el bot de Telegram."""
        try:
            logger.info("Deteniendo bot de Telegram...")
            self.application.stop()
        except Exception as e:
            logger.error(f"Error al detener el bot de Telegram: {e}")
            raise
