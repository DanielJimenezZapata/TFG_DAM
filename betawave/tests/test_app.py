import pytest
import os
import sys
import sqlite3
import tempfile
from flask import url_for, session

# Agregar el directorio raíz del proyecto al path de Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import (
    app, init_db, add_user, verify_user,
    add_song, get_songs, delete_song,
    add_favorite, remove_favorite, get_favorites
)

@pytest.fixture
def client():
    # Configurar la aplicación para pruebas
    app.config['TESTING'] = True
    test_db = os.path.join(tempfile.gettempdir(), 'test_music.db')
    app.config['DATABASE'] = test_db
    
    # Asegurarse de que la base de datos de prueba no existe
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # Inicializar la base de datos
    with app.app_context():
        init_db()
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['_fresh'] = True
        yield client
    
    # Limpiar después de las pruebas
    if os.path.exists(test_db):
        os.remove(test_db)

def test_index_page(client):
    """Prueba que la página principal redirige a login cuando no hay sesión"""
    response = client.get('/')
    # Debería redirigir a login si no hay sesión
    assert response.status_code == 302

def test_register_page(client):
    """Prueba que la página de registro carga correctamente"""
    response = client.get('/register')
    assert response.status_code == 200

def test_login_page(client):
    """Prueba que la página de login carga correctamente"""
    response = client.get('/login')
    assert response.status_code == 200

def test_user_registration(client):
    """Prueba el registro de un nuevo usuario"""
    # Intentar registrar un nuevo usuario
    response = client.post('/register', data={
        'username': 'testuser',
        'password': 'testpass',
        'email': 'test@example.com'
    }, follow_redirects=True)
    assert response.status_code == 200

def test_user_login(client):
    """Prueba el inicio de sesión de un usuario"""
    # Primero registramos un usuario
    client.post('/register', data={
        'username': 'testuser',
        'password': 'testpass',
        'email': 'test@example.com'
    })
    
    # Intentamos iniciar sesión
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)
    assert response.status_code == 200

def test_add_user_function():
    """Prueba la función add_user directamente"""
    test_db = os.path.join(tempfile.gettempdir(), 'test_music.db')
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # Configurar la base de datos de prueba
    with app.app_context():
        app.config['DATABASE'] = test_db
        init_db()
        
        try:
            # Probar agregar un usuario normal
            print("\nIntentando agregar usuario normal...")
            result = add_user('testuser', 'testpass', 'test@example.com', role='user')
            assert result == True, "Debería poder agregar un nuevo usuario"
            
            # Probar agregar un usuario administrador
            print("Intentando agregar usuario administrador...")
            result = add_user('admin2', 'adminpass', 'admin@example.com', role='admin')
            assert result == True, "Debería poder agregar un usuario administrador"
            
            # Probar agregar un usuario duplicado (debe fallar)
            print("Intentando agregar usuario duplicado...")
            result = add_user('testuser', 'testpass', 'test@example.com', role='user')
            assert result == False, "No debería poder agregar un usuario duplicado"
            
            # Verificar el contenido de la base de datos
            conn = sqlite3.connect(test_db)
            c = conn.cursor()
            c.execute("SELECT username, email, role FROM users")
            users = c.fetchall()
            print(f"Usuarios en la base de datos: {users}")
            conn.close()
            
        finally:
            # Limpiar después de la prueba
            if os.path.exists(test_db):
                os.remove(test_db)

def test_verify_user_function():
    """Prueba la función verify_user directamente"""
    test_db = os.path.join(tempfile.gettempdir(), 'test_music.db')
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # Configurar la base de datos de prueba
    with app.app_context():
        app.config['DATABASE'] = test_db
        init_db()
        
        # Agregar un usuario
        add_user('testuser', 'testpass', 'test@example.com')
        
        # Verificar credenciales correctas
        assert verify_user('testuser', 'testpass') is not None
        
        # Verificar credenciales incorrectas
        assert verify_user('testuser', 'wrongpass') is None
        assert verify_user('wronguser', 'testpass') is None

def test_song_management():
    """Prueba la gestión de canciones (agregar, obtener y eliminar)"""
    test_db = os.path.join(tempfile.gettempdir(), 'test_music.db')
    if os.path.exists(test_db):
        os.remove(test_db)
    
    with app.app_context():
        app.config['DATABASE'] = test_db
        init_db()
        
        try:
            # Crear un usuario para las pruebas
            add_user('testuser', 'testpass', 'test@example.com', role='user')
            user = verify_user('testuser', 'testpass')
            assert user is not None, "El usuario debería existir"
            user_id = user['id']
            
            # Probar agregar una canción
            song_id = add_song("Test Song", "Test Artist", "http://example.com/song.mp3", user_id)
            assert song_id is not None, "Debería haberse agregado la canción"
            
            # Obtener las canciones del usuario
            songs = get_songs(user_id)
            assert len(songs) == 1, "Debería haber una canción"
            assert songs[0]['name'] == "Test Song", "El nombre de la canción debería coincidir"
            assert songs[0]['artist'] == "Test Artist", "El artista debería coincidir"
            
            # Eliminar la canción
            success = delete_song(song_id, user_id)
            assert success == True, "La canción debería haberse eliminado"
            
            # Verificar que la canción ya no existe
            songs = get_songs(user_id)
            assert len(songs) == 0, "No deberían quedar canciones"
            
        finally:
            if os.path.exists(test_db):
                os.remove(test_db)

def test_favorites_management():
    """Prueba la gestión de favoritos (agregar, obtener y eliminar)"""
    test_db = os.path.join(tempfile.gettempdir(), 'test_music.db')
    if os.path.exists(test_db):
        os.remove(test_db)
    
    with app.app_context():
        app.config['DATABASE'] = test_db
        init_db()
        print("\nIniciando prueba de favoritos con base de datos:", test_db)
        
        try:
            # Crear un usuario para las pruebas
            add_user('testuser', 'testpass', 'test@example.com', role='user')
            user = verify_user('testuser', 'testpass')
            assert user is not None, "El usuario debería existir"
            user_id = user['id']
            
            # Agregar una canción primero
            test_song = {
                'name': "Test Song",
                'artist': "Test Artist",
                'url': "http://example.com/song.mp3"
            }
            
            # Verificar que inicialmente no hay canciones
            songs = get_songs(user_id)
            assert len(songs) == 0, "No debería haber canciones inicialmente"
            
            # Agregar la canción
            song_id = add_song(test_song['name'], test_song['artist'], test_song['url'], user_id)
            assert song_id is not None, "Debería haberse agregado la canción"
            
            # Verificar que la canción se agregó correctamente
            songs = get_songs(user_id)
            assert len(songs) == 1, "Debería haber una canción"
            assert songs[0]['name'] == test_song['name'], "El nombre de la canción debería coincidir"
            
            # Verificar que inicialmente no hay favoritos
            favorites = get_favorites(user_id)
            assert len(favorites) == 0, "No debería haber favoritos inicialmente"
            
            # Agregar a favoritos
            success = add_favorite(user_id, song_id)
            assert success == True, "Debería haberse agregado a favoritos"
              # Verificar que está en favoritos
            favorites = get_favorites(user_id)
            print(f"\nFavoritos después de agregar: {favorites}")
            print(f"ID de usuario: {user_id}, ID de canción: {song_id}")
            # Verificar directo en la base de datos
            conn = sqlite3.connect(test_db)
            c = conn.cursor()
            c.execute("SELECT * FROM favorites WHERE user_id=? AND song_id=?", (user_id, song_id))
            fav_row = c.fetchone()
            print(f"Registro en tabla favorites: {fav_row}")
            conn.close()
            
            assert len(favorites) == 1, "Debería haber un favorito"
            assert favorites[0]['id'] == song_id, "El ID de la canción debería coincidir"
            assert favorites[0]['name'] == test_song['name'], "El nombre de la canción debería coincidir"
            
            # Eliminar de favoritos
            success = remove_favorite(user_id, song_id)
            assert success == True, "Debería haberse eliminado de favoritos"
            
            # Verificar que ya no está en favoritos
            favorites = get_favorites(user_id)
            assert len(favorites) == 0, "No deberían quedar favoritos"
            
        finally:
            if os.path.exists(test_db):
                os.remove(test_db)

def login_test_user(client):
    """Helper function para login de usuario de prueba"""
    # Registrar un usuario
    client.post('/register', data={
        'username': 'testuser',
        'password': 'testpass',
        'email': 'test@example.com'
    })
    
    # Iniciar sesión
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)
    
    return verify_user('testuser', 'testpass')

def test_song_api_routes(client):
    """Prueba las rutas de la API relacionadas con canciones"""
    # Login y obtener usuario
    user = login_test_user(client)
    assert user is not None, "El usuario debería estar autenticado"
    
    with client.session_transaction() as sess:
        sess['user_id'] = user['id']
        sess['username'] = user['username']
        sess['role'] = user['role']    # Probar obtener la lista de canciones (inicialmente vacía)
    response = client.get('/api/songs')
    assert response.status_code == 200, "Debería poder obtener la lista de canciones"
    
    # Agregar una canción de prueba
    test_song_id = add_song("Test Song", "Test Artist", "http://example.com/test.mp3", sess['user_id'])
    assert test_song_id is not None, "Debería poder agregar una canción"
    
    # Verificar que la canción aparece en la lista
    response = client.get('/api/songs')
    assert response.status_code == 200, "Debería poder obtener la lista de canciones"
    songs = response.get_json()
    assert len(songs) > 0, "Debería haber al menos una canción"
    assert any(song['name'] == "Test Song" for song in songs), "La canción de prueba debería estar en la lista"

def test_favorites_api_routes(client):
    """Prueba las rutas de la API relacionadas con favoritos"""
    # Login y obtener usuario
    user = login_test_user(client)
    assert user is not None, "El usuario debería estar autenticado"

    with client.session_transaction() as sess:
        sess['user_id'] = user['id']
        sess['username'] = user['username']
        sess['role'] = user['role']

    # Agregar una canción para las pruebas
    test_song = {
        'name': "Test Song",
        'artist': "Test Artist",
        'url': "http://example.com/test.mp3"
    }
    song_id = add_song(test_song['name'], test_song['artist'], test_song['url'], user['id'])
    assert song_id is not None, "Debería poder agregar una canción"

    # Verificar lista inicial de favoritos
    response = client.get('/api/favorites')
    assert response.status_code == 200, "Debería poder obtener la lista de favoritos"
    favorites = response.get_json()
    assert len(favorites) == 0, "No debería haber favoritos inicialmente"

    # Verificar estado inicial de favorito
    response = client.post('/api/is_favorite', json={'song_id': song_id})
    assert response.status_code == 200, "Debería poder verificar estado de favorito"
    assert response.get_json()['is_favorite'] == False, "No debería ser favorito inicialmente"

    # Agregar a favoritos usando toggle_favorite
    response = client.post('/api/toggle_favorite', 
                         json={'song_id': song_id})
    assert response.status_code == 200, "Debería poder agregar a favoritos"
    assert response.get_json()['is_favorite'] == True, "La respuesta debería indicar que es favorito"

    # Verificar que se agregó a favoritos
    response = client.get('/api/favorites')
    assert response.status_code == 200, "Debería poder obtener la lista de favoritos"
    favorites = response.get_json()
    assert len(favorites) == 1, "Debería haber un favorito"
    assert favorites[0]['id'] == song_id, "El ID de la canción debería coincidir"
    assert favorites[0]['name'] == test_song['name'], "El nombre de la canción debería coincidir"
    assert favorites[0]['artist'] == test_song['artist'], "El artista de la canción debería coincidir"

    # Verificar estado de favorito con is_favorite
    response = client.post('/api/is_favorite', json={'song_id': song_id})
    assert response.status_code == 200, "Debería poder verificar estado de favorito"
    assert response.get_json()['is_favorite'] == True, "Debería estar marcado como favorito"

    # Eliminar de favoritos usando toggle_favorite nuevamente
    response = client.post('/api/toggle_favorite', 
                         json={'song_id': song_id})
    assert response.status_code == 200, "Debería poder eliminar de favoritos"
    assert response.get_json()['is_favorite'] == False, "La respuesta debería indicar que ya no es favorito"

    # Verificar que se eliminó de favoritos
    response = client.get('/api/favorites')
    assert response.status_code == 200, "Debería poder obtener la lista de favoritos"
    favorites = response.get_json()
    assert len(favorites) == 0, "No deberían quedar favoritos"

    # Verificar estado final de favorito
    response = client.post('/api/is_favorite', json={'song_id': song_id})
    assert response.status_code == 200, "Debería poder verificar estado de favorito"
    assert response.get_json()['is_favorite'] == False, "No debería estar marcado como favorito"
