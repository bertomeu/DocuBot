"""
Esquema de la base de datos para DocuBot.
Define las tablas y relaciones necesarias para almacenar la configuración del bot
y los documentos para consulta.
"""

import os
import sqlite3
from datetime import datetime

class DatabaseManager:
    """Gestiona la conexión y operaciones con la base de datos SQLite."""
    
    def __init__(self, db_path):
        """
        Inicializa el gestor de base de datos.
        
        Args:
            db_path (str): Ruta al archivo de base de datos SQLite.
        """
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Establece conexión con la base de datos."""
        try:
            # Asegurarse de que el directorio existe
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Conectar a la base de datos
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Para acceder a las columnas por nombre
            self.cursor = self.connection.cursor()
            return True
        except sqlite3.Error as e:
            print(f"Error al conectar a la base de datos: {e}")
            return False
    
    def disconnect(self):
        """Cierra la conexión con la base de datos."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None
    
    def create_tables(self):
        """Crea las tablas necesarias en la base de datos si no existen."""
        try:
            # Tabla para la configuración del bot
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_config (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                instructions TEXT,
                platform TEXT CHECK(platform IN ('whatsapp', 'telegram', 'both')),
                openai_api_key TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Tabla para los documentos
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Tabla para los chunks de documentos (para búsqueda eficiente)
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                embedding_file TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
            )
            ''')
            
            # Tabla para las conversaciones
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Tabla para los mensajes
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                conversation_id INTEGER NOT NULL,
                is_from_user BOOLEAN NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
            )
            ''')
            
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error al crear las tablas: {e}")
            self.connection.rollback()
            return False
    
    def initialize_config(self, name="DocuBot", description="Asistente de documentación basado en IA", 
                         instructions="Responde preguntas basadas en la documentación proporcionada.", 
                         platform="both"):
        """
        Inicializa la configuración del bot con valores predeterminados si no existe.
        
        Args:
            name (str): Nombre del bot.
            description (str): Descripción del bot.
            instructions (str): Instrucciones para el comportamiento del bot.
            platform (str): Plataforma de mensajería ('whatsapp', 'telegram', 'both').
        
        Returns:
            bool: True si la operación fue exitosa, False en caso contrario.
        """
        try:
            # Verificar si ya existe una configuración
            self.cursor.execute("SELECT COUNT(*) FROM bot_config")
            count = self.cursor.fetchone()[0]
            
            if count == 0:
                # Insertar configuración predeterminada
                self.cursor.execute('''
                INSERT INTO bot_config (name, description, instructions, platform)
                VALUES (?, ?, ?, ?)
                ''', (name, description, instructions, platform))
                self.connection.commit()
            
            return True
        except sqlite3.Error as e:
            print(f"Error al inicializar la configuración: {e}")
            self.connection.rollback()
            return False
    
    def execute_query(self, query, params=None):
        """
        Ejecuta una consulta SQL personalizada.
        
        Args:
            query (str): Consulta SQL a ejecutar.
            params (tuple, optional): Parámetros para la consulta.
        
        Returns:
            list: Resultados de la consulta.
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            if query.strip().upper().startswith(("SELECT", "PRAGMA")):
                return [dict(row) for row in self.cursor.fetchall()]
            else:
                self.connection.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            if not query.strip().upper().startswith(("SELECT", "PRAGMA")):
                self.connection.rollback()
            return False
