"""
Módulo para integrar consultas y respuestas con OpenAI en DocuBot.
Proporciona funciones para procesar consultas de usuarios y generar respuestas contextuales.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Añadir el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent.parent))

from src.openai.openai_manager import OpenAIManager
from src.openai.document_processor import DocumentProcessor
from src.database.document_manager import DocumentManager

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

class QueryProcessor:
    """Procesa consultas de usuarios y genera respuestas utilizando OpenAI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el procesador de consultas.
        
        Args:
            api_key (str, optional): Clave de API de OpenAI.
                                    Si no se proporciona, se intenta obtener de las variables de entorno.
        """
        try:
            # Inicializar gestores
            self.openai_manager = OpenAIManager(api_key)
            self.document_processor = DocumentProcessor()
            self.document_manager = DocumentManager()
            
            logger.info("QueryProcessor inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar QueryProcessor: {e}")
            raise
    
    def process_query(self, query: str, document_id: Optional[str] = None) -> str:
        """
        Procesa una consulta y genera una respuesta.
        
        Args:
            query (str): Consulta del usuario.
            document_id (str, optional): ID del documento específico para buscar.
                                        Si no se proporciona, se busca en todos los documentos.
            
        Returns:
            str: Respuesta a la consulta.
        """
        try:
            # Verificar si se debe buscar en un documento específico o en todos
            if document_id:
                # Buscar en un documento específico
                answer = self.openai_manager.search_in_document(document_id, query)
                if answer is None:
                    return "Lo siento, no pude encontrar información relevante en ese documento."
            else:
                # Buscar en todos los documentos
                answer = self.openai_manager.search_in_all_documents(query)
                if answer is None:
                    # Si no hay documentos procesados, usar la API directamente
                    answer = self.openai_manager.process_query(query)
            
            return answer
        
        except Exception as e:
            logger.error(f"Error al procesar la consulta: {e}")
            return "Lo siento, ocurrió un error al procesar tu consulta. Por favor, inténtalo de nuevo."
    
    def upload_and_process_document(self, file_path: str, title: str, description: str = "") -> Optional[int]:
        """
        Sube y procesa un documento PDF.
        
        Args:
            file_path (str): Ruta al archivo PDF.
            title (str): Título del documento.
            description (str, optional): Descripción del documento.
            
        Returns:
            int or None: ID del documento procesado, o None si hubo un error.
        """
        try:
            # Verificar que el archivo existe
            if not os.path.isfile(file_path):
                logger.error(f"El archivo {file_path} no existe")
                return None
            
            # Verificar que es un archivo PDF
            if not file_path.lower().endswith('.pdf'):
                logger.error(f"El archivo {file_path} no es un PDF")
                return None
            
            # Añadir el documento a la base de datos
            document_id = self.document_manager.add_document(title, file_path, description)
            if document_id is None:
                logger.error(f"Error al añadir el documento {file_path} a la base de datos")
                return None
            
            # Guardar una copia del documento
            document_id_str = str(document_id)
            if not self.document_processor.save_processed_document(file_path, document_id_str):
                logger.error(f"Error al guardar el documento {file_path}")
                return None
            
            # Procesar el documento con OpenAI
            if not self.openai_manager.process_document(file_path):
                logger.error(f"Error al procesar el documento {file_path} con OpenAI")
                return None
            
            logger.info(f"Documento {file_path} procesado correctamente (ID: {document_id})")
            return document_id
        
        except Exception as e:
            logger.error(f"Error al subir y procesar el documento {file_path}: {e}")
            return None
    
    def generate_document_summary(self, document_id: int) -> Optional[str]:
        """
        Genera un resumen de un documento.
        
        Args:
            document_id (int): ID del documento.
            
        Returns:
            str or None: Resumen del documento, o None si hubo un error.
        """
        try:
            # Obtener información del documento
            document = self.document_manager.get_document(document_id)
            if document is None:
                logger.error(f"No existe un documento con ID {document_id}")
                return None
            
            # Extraer texto del documento
            text, _ = self.document_processor.process_pdf(document['file_path'])
            if text is None:
                logger.error(f"Error al extraer texto del documento {document_id}")
                return None
            
            # Limitar el texto para el resumen (primeros 4000 caracteres)
            text_for_summary = text[:4000]
            
            # Generar resumen con OpenAI
            summary_query = f"Genera un resumen conciso del siguiente documento: {text_for_summary}"
            summary = self.openai_manager.process_query(summary_query)
            
            return summary
        
        except Exception as e:
            logger.error(f"Error al generar resumen del documento {document_id}: {e}")
            return None
