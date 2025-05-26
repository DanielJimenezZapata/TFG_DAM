import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile
import sqlite3
from app import app, init_db, add_user, verify_user

@pytest.fixture(scope="session")
def app_configured():
    """Fixture para configurar la aplicación Flask"""
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False
    })
    return app

@pytest.fixture(scope="function")
def app_context(app_configured):
    """Fixture para el contexto de la aplicación"""
    with app_configured.app_context() as ctx:
        yield ctx

@pytest.fixture(scope="function")
def test_db(app_context):
    """Fixture para la base de datos de prueba"""
    db_path = os.path.join(tempfile.gettempdir(), 'test_music.db')
    
    # Limpiar base de datos anterior si existe
    if os.path.exists(db_path):
        os.unlink(db_path)
    
    # Configurar la base de datos de prueba
    app.config['DATABASE'] = db_path
    
    # Inicializar la base de datos
    init_db()
    
    # Verificar que las tablas se crearon correctamente
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Verificar cada tabla
    tables = ['users', 'songs', 'favorites', 'user_config']
    for table in tables:
        c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        result = c.fetchone()
        assert result is not None, f"La tabla {table} no se creó correctamente"
    
    conn.close()
    
    # Crear usuario de prueba
    success = add_user('testuser', 'testpass', 'test@example.com', role='user')
    assert success, "No se pudo crear el usuario de prueba"
    
    # Verificar que el admin existe
    admin = verify_user('admin', 'admin123')
    assert admin is not None, "El usuario admin no existe"
    
    yield db_path
    
    # Limpiar después de cada prueba
    if os.path.exists(db_path):
        os.unlink(db_path)

@pytest.fixture(scope="function")
def client(app_configured, test_db):
    """Fixture para el cliente de pruebas"""
    return app_configured.test_client()
