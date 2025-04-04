"""
Módulo para procesar documentos PDF y extraer su contenido.
Proporciona funciones para cargar, procesar y extraer texto de documentos PDF.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Añadir el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent.parent))

# Importar módulos para procesamiento de PDF
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter

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

class DocumentProcessor:
    """Procesa documentos PDF y extrae su contenido."""
    
    def __init__(self):
        """Inicializa el procesador de documentos."""
        # Directorio para almacenar documentos procesados
        self.documents_dir = os.path.join(Path(__file__).parent.parent.parent, 'data', 'documents')
        os.makedirs(self.documents_dir, exist_ok=True)
        
        # Inicializar el divisor de texto
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        logger.info("DocumentProcessor inicializado correctamente")
    
    def extract_text_from_pdf(self, file_path: str) -> Optional[str]:
        """
        Extrae el texto de un archivo PDF.
        
        Args:
            file_path (str): Ruta al archivo PDF.
            
        Returns:
            str or None: Texto extraído del PDF, o None si hubo un error.
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
            
            # Extraer texto del PDF
            reader = PdfReader(file_path)
            text = ""
            
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            logger.info(f"Texto extraído correctamente del archivo {file_path}")
            return text
        
        except Exception as e:
            logger.error(f"Error al extraer texto del archivo {file_path}: {e}")
            return None
    
    def split_text_into_chunks(self, text: str) -> List[str]:
        """
        Divide el texto en chunks para su procesamiento.
        
        Args:
            text (str): Texto a dividir.
            
        Returns:
            list: Lista de chunks de texto.
        """
        try:
            # Dividir el texto en chunks
            chunks = self.text_splitter.split_text(text)
            
            logger.info(f"Texto dividido en {len(chunks)} chunks")
            return chunks
        
        except Exception as e:
            logger.error(f"Error al dividir el texto en chunks: {e}")
            return []
    
    def process_pdf(self, file_path: str, save_chunks: bool = False) -> Tuple[Optional[str], Optional[List[str]]]:
        """
        Procesa un archivo PDF: extrae el texto y lo divide en chunks.
        
        Args:
            file_path (str): Ruta al archivo PDF.
            save_chunks (bool, optional): Si es True, guarda los chunks en archivos separados.
            
        Returns:
            tuple: (texto completo, lista de chunks), o (None, None) si hubo un error.
        """
        try:
            # Extraer texto del PDF
            text = self.extract_text_from_pdf(file_path)
            if text is None:
                return None, None
            
            # Dividir el texto en chunks
            chunks = self.split_text_into_chunks(text)
            if not chunks:
                return text, []
            
            # Guardar chunks en archivos separados si se solicita
            if save_chunks:
                document_id = os.path.basename(file_path).replace('.pdf', '')
                chunks_dir = os.path.join(self.documents_dir, document_id, 'chunks')
                os.makedirs(chunks_dir, exist_ok=True)
                
                for i, chunk in enumerate(chunks):
                    chunk_file = os.path.join(chunks_dir, f"chunk_{i:04d}.txt")
                    with open(chunk_file, 'w', encoding='utf-8') as f:
                        f.write(chunk)
                
                logger.info(f"Chunks guardados en {chunks_dir}")
            
            return text, chunks
        
        except Exception as e:
            logger.error(f"Error al procesar el archivo {file_path}: {e}")
            return None, None
    
    def save_processed_document(self, file_path: str, document_id: str) -> bool:
        """
        Guarda una copia del documento procesado en el directorio de documentos.
        
        Args:
            file_path (str): Ruta al archivo PDF original.
            document_id (str): ID del documento.
            
        Returns:
            bool: True si la operación fue exitosa, False en caso contrario.
        """
        try:
            # Verificar que el archivo existe
            if not os.path.isfile(file_path):
                logger.error(f"El archivo {file_path} no existe")
                return False
            
            # Crear directorio para el documento
            document_dir = os.path.join(self.documents_dir, document_id)
            os.makedirs(document_dir, exist_ok=True)
            
            # Copiar el archivo
            import shutil
            dest_path = os.path.join(document_dir, os.path.basename(file_path))
            shutil.copy2(file_path, dest_path)
            
            logger.info(f"Documento guardado en {dest_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error al guardar el documento {file_path}: {e}")
            return False
