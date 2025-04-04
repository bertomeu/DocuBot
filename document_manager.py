"""
Módulo para gestionar documentos en la base de datos.
Proporciona funciones para añadir, actualizar, eliminar y consultar documentos.
"""

import os
import sys
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Añadir el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.database.schema import DatabaseManager

class DocumentManager:
    """Gestiona las operaciones relacionadas con documentos en la base de datos."""
    
    def __init__(self, db_path=None):
        """
        Inicializa el gestor de documentos.
        
        Args:
            db_path (str, optional): Ruta al archivo de base de datos SQLite.
                                    Si no se proporciona, se usa la ruta predeterminada.
        """
        if db_path is None:
            base_dir = Path(__file__).parent.parent.parent
            db_path = os.path.join(base_dir, 'data', 'docubot.db')
        
        self.db_manager = DatabaseManager(db_path)
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        Calcula el hash MD5 de un archivo.
        
        Args:
            file_path (str): Ruta al archivo.
            
        Returns:
            str: Hash MD5 del archivo.
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def add_document(self, title: str, file_path: str, description: str = "") -> Optional[int]:
        """
        Añade un nuevo documento a la base de datos.
        
        Args:
            title (str): Título del documento.
            file_path (str): Ruta al archivo del documento.
            description (str, optional): Descripción del documento.
            
        Returns:
            int or None: ID del documento añadido, o None si hubo un error.
        """
        try:
            # Verificar que el archivo existe
            if not os.path.isfile(file_path):
                print(f"Error: El archivo {file_path} no existe.")
                return None
            
            # Determinar el tipo de archivo
            file_type = os.path.splitext(file_path)[1].lower().lstrip('.')
            
            # Calcular el hash del archivo
            content_hash = self._calculate_file_hash(file_path)
            
            # Conectar a la base de datos
            if not self.db_manager.connect():
                return None
            
            # Verificar si el documento ya existe (por hash)
            self.db_manager.cursor.execute(
                "SELECT id FROM documents WHERE content_hash = ?", 
                (content_hash,)
            )
            existing_doc = self.db_manager.cursor.fetchone()
            
            if existing_doc:
                print(f"Advertencia: Ya existe un documento con el mismo contenido (ID: {existing_doc['id']}).")
                self.db_manager.disconnect()
                return existing_doc['id']
            
            # Insertar el nuevo documento
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.db_manager.cursor.execute('''
            INSERT INTO documents (title, description, file_path, file_type, content_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, description, file_path, file_type, content_hash, current_time, current_time))
            
            self.db_manager.connection.commit()
            document_id = self.db_manager.cursor.lastrowid
            
            # Desconectar de la base de datos
            self.db_manager.disconnect()
            
            return document_id
        
        except sqlite3.Error as e:
            print(f"Error al añadir el documento: {e}")
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
                self.db_manager.disconnect()
            return None
    
    def update_document(self, document_id: int, title: str = None, description: str = None) -> bool:
        """
        Actualiza la información de un documento existente.
        
        Args:
            document_id (int): ID del documento a actualizar.
            title (str, optional): Nuevo título del documento.
            description (str, optional): Nueva descripción del documento.
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario.
        """
        try:
            # Verificar que se proporcionó al menos un campo para actualizar
            if title is None and description is None:
                print("Error: Debe proporcionar al menos un campo para actualizar.")
                return False
            
            # Conectar a la base de datos
            if not self.db_manager.connect():
                return False
            
            # Verificar que el documento existe
            self.db_manager.cursor.execute(
                "SELECT id FROM documents WHERE id = ?", 
                (document_id,)
            )
            if not self.db_manager.cursor.fetchone():
                print(f"Error: No existe un documento con ID {document_id}.")
                self.db_manager.disconnect()
                return False
            
            # Construir la consulta de actualización
            update_fields = []
            params = []
            
            if title is not None:
                update_fields.append("title = ?")
                params.append(title)
            
            if description is not None:
                update_fields.append("description = ?")
                params.append(description)
            
            # Añadir la fecha de actualización
            update_fields.append("updated_at = ?")
            params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # Añadir el ID del documento
            params.append(document_id)
            
            # Ejecutar la consulta
            query = f"UPDATE documents SET {', '.join(update_fields)} WHERE id = ?"
            self.db_manager.cursor.execute(query, params)
            self.db_manager.connection.commit()
            
            # Desconectar de la base de datos
            self.db_manager.disconnect()
            
            return True
        
        except sqlite3.Error as e:
            print(f"Error al actualizar el documento: {e}")
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
                self.db_manager.disconnect()
            return False
    
    def delete_document(self, document_id: int) -> bool:
        """
        Elimina un documento de la base de datos.
        
        Args:
            document_id (int): ID del documento a eliminar.
            
        Returns:
            bool: True si la eliminación fue exitosa, False en caso contrario.
        """
        try:
            # Conectar a la base de datos
            if not self.db_manager.connect():
                return False
            
            # Verificar que el documento existe
            self.db_manager.cursor.execute(
                "SELECT file_path FROM documents WHERE id = ?", 
                (document_id,)
            )
            document = self.db_manager.cursor.fetchone()
            
            if not document:
                print(f"Error: No existe un documento con ID {document_id}.")
                self.db_manager.disconnect()
                return False
            
            # Eliminar el documento
            self.db_manager.cursor.execute(
                "DELETE FROM documents WHERE id = ?", 
                (document_id,)
            )
            self.db_manager.connection.commit()
            
            # Desconectar de la base de datos
            self.db_manager.disconnect()
            
            return True
        
        except sqlite3.Error as e:
            print(f"Error al eliminar el documento: {e}")
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
                self.db_manager.disconnect()
            return False
    
    def get_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene la información de un documento.
        
        Args:
            document_id (int): ID del documento a obtener.
            
        Returns:
            dict or None: Información del documento, o None si no existe o hubo un error.
        """
        try:
            # Conectar a la base de datos
            if not self.db_manager.connect():
                return None
            
            # Obtener el documento
            self.db_manager.cursor.execute(
                "SELECT * FROM documents WHERE id = ?", 
                (document_id,)
            )
            document = self.db_manager.cursor.fetchone()
            
            # Desconectar de la base de datos
            self.db_manager.disconnect()
            
            if document:
                return dict(document)
            else:
                print(f"No existe un documento con ID {document_id}.")
                return None
        
        except sqlite3.Error as e:
            print(f"Error al obtener el documento: {e}")
            if self.db_manager.connection:
                self.db_manager.disconnect()
            return None
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los documentos de la base de datos.
        
        Returns:
            list: Lista de diccionarios con la información de los documentos.
        """
        try:
            # Conectar a la base de datos
            if not self.db_manager.connect():
                return []
            
            # Obtener todos los documentos
            self.db_manager.cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
            documents = [dict(row) for row in self.db_manager.cursor.fetchall()]
            
            # Desconectar de la base de datos
            self.db_manager.disconnect()
            
            return documents
        
        except sqlite3.Error as e:
            print(f"Error al obtener los documentos: {e}")
            if self.db_manager.connection:
                self.db_manager.disconnect()
            return []
    
    def search_documents(self, query: str) -> List[Dict[str, Any]]:
        """
        Busca documentos que coincidan con la consulta.
        
        Args:
            query (str): Texto a buscar en el título o descripción de los documentos.
            
        Returns:
            list: Lista de diccionarios con la información de los documentos encontrados.
        """
        try:
            # Conectar a la base de datos
            if not self.db_manager.connect():
                return []
            
            # Buscar documentos
            search_term = f"%{query}%"
            self.db_manager.cursor.execute(
                "SELECT * FROM documents WHERE title LIKE ? OR description LIKE ? ORDER BY created_at DESC", 
                (search_term, search_term)
            )
            documents = [dict(row) for row in self.db_manager.cursor.fetchall()]
            
            # Desconectar de la base de datos
            self.db_manager.disconnect()
            
            return documents
        
        except sqlite3.Error as e:
            print(f"Error al buscar documentos: {e}")
            if self.db_manager.connection:
                self.db_manager.disconnect()
            return []
