"""
Módulo para integrar la API de OpenAI en DocuBot.
Proporciona funciones para procesar consultas utilizando la API de OpenAI.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Añadir el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent.parent))

# Importar módulos de OpenAI y LangChain
import openai
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import PyPDFLoader

from src.bot.env_manager import EnvManager

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

class OpenAIManager:
    """Gestiona la integración con la API de OpenAI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el gestor de OpenAI.
        
        Args:
            api_key (str, optional): Clave de API de OpenAI.
                                    Si no se proporciona, se intenta obtener de las variables de entorno.
        """
        # Cargar la clave de API
        if api_key is None:
            env_manager = EnvManager()
            api_key = env_manager.get_openai_api_key()
        
        self.api_key = api_key
        
        # Verificar que se ha proporcionado una clave de API
        if not self.api_key:
            logger.error("No se ha proporcionado una clave de API de OpenAI")
            raise ValueError("Se requiere una clave de API de OpenAI")
        
        # Configurar la API de OpenAI
        openai.api_key = self.api_key
        
        # Directorio para almacenar los índices de vectores
        self.vector_store_dir = os.path.join(Path(__file__).parent.parent.parent, 'data', 'vector_store')
        os.makedirs(self.vector_store_dir, exist_ok=True)
        
        # Inicializar el modelo de chat
        self.chat_model = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            openai_api_key=self.api_key
        )
        
        # Inicializar el embeddings model
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.api_key)
        
        logger.info("OpenAIManager inicializado correctamente")
    
    def process_query(self, query: str, context: Optional[str] = None) -> str:
        """
        Procesa una consulta utilizando la API de OpenAI.
        
        Args:
            query (str): Consulta a procesar.
            context (str, optional): Contexto adicional para la consulta.
            
        Returns:
            str: Respuesta a la consulta.
        """
        try:
            # Preparar el mensaje para la API
            messages = [
                {"role": "system", "content": "Eres un asistente útil que responde preguntas basadas en la documentación proporcionada."}
            ]
            
            # Añadir contexto si se proporciona
            if context:
                messages.append({"role": "system", "content": f"Contexto: {context}"})
            
            # Añadir la consulta del usuario
            messages.append({"role": "user", "content": query})
            
            # Realizar la llamada a la API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            # Extraer la respuesta
            answer = response.choices[0].message.content.strip()
            
            return answer
        
        except Exception as e:
            logger.error(f"Error al procesar la consulta con OpenAI: {e}")
            return "Lo siento, ocurrió un error al procesar tu consulta. Por favor, inténtalo de nuevo."
    
    def process_document(self, file_path: str) -> bool:
        """
        Procesa un documento PDF y crea un índice de vectores para búsqueda.
        
        Args:
            file_path (str): Ruta al archivo PDF.
            
        Returns:
            bool: True si el procesamiento fue exitoso, False en caso contrario.
        """
        try:
            # Verificar que el archivo existe
            if not os.path.isfile(file_path):
                logger.error(f"El archivo {file_path} no existe")
                return False
            
            # Verificar que es un archivo PDF
            if not file_path.lower().endswith('.pdf'):
                logger.error(f"El archivo {file_path} no es un PDF")
                return False
            
            # Cargar el documento
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            
            # Dividir el texto en chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len
            )
            chunks = text_splitter.split_documents(documents)
            
            # Crear el índice de vectores
            document_id = os.path.basename(file_path).replace('.pdf', '')
            vector_store_path = os.path.join(self.vector_store_dir, f"{document_id}")
            
            # Crear el índice de vectores
            vector_store = FAISS.from_documents(chunks, self.embeddings)
            
            # Guardar el índice de vectores
            vector_store.save_local(vector_store_path)
            
            logger.info(f"Documento {file_path} procesado correctamente")
            return True
        
        except Exception as e:
            logger.error(f"Error al procesar el documento {file_path}: {e}")
            return False
    
    def search_in_document(self, document_id: str, query: str) -> Optional[str]:
        """
        Busca en un documento procesado.
        
        Args:
            document_id (str): ID del documento.
            query (str): Consulta a buscar.
            
        Returns:
            str or None: Resultado de la búsqueda, o None si hubo un error.
        """
        try:
            # Verificar que existe el índice de vectores
            vector_store_path = os.path.join(self.vector_store_dir, f"{document_id}")
            if not os.path.isdir(vector_store_path):
                logger.error(f"No existe el índice de vectores para el documento {document_id}")
                return None
            
            # Cargar el índice de vectores
            vector_store = FAISS.load_local(vector_store_path, self.embeddings)
            
            # Crear el retriever
            retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})
            
            # Crear la cadena de recuperación
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.chat_model,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True
            )
            
            # Realizar la búsqueda
            result = qa_chain({"query": query})
            
            # Extraer la respuesta
            answer = result["result"]
            
            return answer
        
        except Exception as e:
            logger.error(f"Error al buscar en el documento {document_id}: {e}")
            return None
    
    def search_in_all_documents(self, query: str) -> Optional[str]:
        """
        Busca en todos los documentos procesados.
        
        Args:
            query (str): Consulta a buscar.
            
        Returns:
            str or None: Resultado de la búsqueda, o None si hubo un error.
        """
        try:
            # Obtener todos los índices de vectores
            vector_stores = []
            for document_id in os.listdir(self.vector_store_dir):
                vector_store_path = os.path.join(self.vector_store_dir, document_id)
                if os.path.isdir(vector_store_path):
                    vector_store = FAISS.load_local(vector_store_path, self.embeddings)
                    vector_stores.append(vector_store)
            
            # Verificar que hay al menos un índice de vectores
            if not vector_stores:
                logger.warning("No hay documentos procesados")
                return "No hay documentos procesados para buscar. Por favor, sube algún documento primero."
            
            # Combinar los índices de vectores
            combined_vector_store = vector_stores[0]
            for vector_store in vector_stores[1:]:
                combined_vector_store.merge_from(vector_store)
            
            # Crear el retriever
            retriever = combined_vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})
            
            # Crear la cadena de recuperación
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.chat_model,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True
            )
            
            # Realizar la búsqueda
            result = qa_chain({"query": query})
            
            # Extraer la respuesta
            answer = result["result"]
            
            return answer
        
        except Exception as e:
            logger.error(f"Error al buscar en todos los documentos: {e}")
            return None
