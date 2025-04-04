"""
Script para inicializar la base de datos de DocuBot.
Crea la base de datos y las tablas necesarias si no existen.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Añadir el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.database.schema import DatabaseManager

def initialize_database():
    """
    Inicializa la base de datos con la estructura necesaria.
    
    Returns:
        bool: True si la inicialización fue exitosa, False en caso contrario.
    """
    # Definir la ruta de la base de datos
    base_dir = Path(__file__).parent.parent.parent
    db_path = os.path.join(base_dir, 'data', 'docubot.db')
    
    # Crear el directorio de datos si no existe
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Inicializar el gestor de base de datos
    db_manager = DatabaseManager(db_path)
    
    # Conectar a la base de datos
    if not db_manager.connect():
        print("Error: No se pudo conectar a la base de datos.")
        return False
    
    # Crear las tablas
    if not db_manager.create_tables():
        print("Error: No se pudieron crear las tablas en la base de datos.")
        db_manager.disconnect()
        return False
    
    # Inicializar la configuración predeterminada
    if not db_manager.initialize_config():
        print("Error: No se pudo inicializar la configuración del bot.")
        db_manager.disconnect()
        return False
    
    # Desconectar de la base de datos
    db_manager.disconnect()
    
    print(f"Base de datos inicializada correctamente en: {db_path}")
    return True

if __name__ == "__main__":
    # Si se ejecuta directamente, inicializar la base de datos
    success = initialize_database()
    if success:
        print("Inicialización completada con éxito.")
    else:
        print("La inicialización falló.")
        sys.exit(1)
