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
    add_favorite, remove_favorite, get_favorites,
    search_songs
)

# Las fixtures ahora están en conftest.py

@pytest.fixture
def client(test_db):
    """Fixture para el cliente de pruebas"""
    with app.test_client() as client:
        yield client

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

    # Verificar estado de favorito with is_favorite
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

def test_user_config(client):
    """Prueba la gestión de configuración del usuario"""
    # Login
    user = login_test_user(client)
    assert user is not None, "El usuario debería estar autenticado"

    with client.session_transaction() as sess:
        sess['user_id'] = user['id']
        sess['username'] = user['username']

    # Verificar configuración inicial
    response = client.get('/config')
    assert response.status_code == 200, "Debería poder acceder a la página de configuración"

    # Guardar nueva configuración
    config_data = {
        'darkMode': True,
        'defaultVolume': 75
    }
    response = client.post('/save_config', 
                         json=config_data,
                         follow_redirects=True)
    assert response.status_code == 200, "Debería poder guardar la configuración"
    assert response.get_json()['success'] == True, "La configuración debería guardarse correctamente"

    # Verificar que la configuración se guardó
    response = client.get('/config')
    assert response.status_code == 200, "Debería poder acceder a la configuración"
    assert b'value="75"' in response.data, "El volumen debería haberse actualizado"

def test_profile_management(client, test_db, app_context):
    """Prueba la gestión del perfil de usuario"""
    
    print(f"\n[test_profile_management] Using test DB: {test_db}")
    
    # Ensure we're using the test database
    app.config['DATABASE'] = test_db
    
    # Initialize the database
    with app.app_context():
        # Crear un usuario de prueba con un nombre único
        success = add_user('profileuser', 'testpass', 'profile@example.com', role='user')
        assert success, "Debería poder crear un usuario de prueba"
        
        # Login como usuario de prueba
        user = verify_user('profileuser', 'testpass')
        assert user is not None, "El usuario debería existir"
        
        with client.session_transaction() as sess:
            sess['user_id'] = user['id']
            sess['username'] = user['username']
            sess['user_role'] = 'user'
        
        # Verificar acceso al perfil
        response = client.get('/profile')
        assert response.status_code == 200, "Debería poder acceder al perfil"
        assert b'profileuser' in response.data, "El nombre de usuario debería mostrarse"
        
        # Actualizar perfil
        profile_data = {
            'username': 'updateduser',
            'email': 'updated@example.com',
            'current_password': 'testpass',
            'new_password': 'newpass',
            'repeat_password': 'newpass'
        }
        response = client.post('/profile', 
                             data=profile_data,
                             follow_redirects=True)
        assert response.status_code == 200, "Debería poder actualizar el perfil"
        assert b'Perfil actualizado correctamente' in response.data, "Debería mostrar mensaje de éxito"
        
        # Verificar que los cambios se aplicaron
        conn = sqlite3.connect(test_db)
        c = conn.cursor()
        c.execute("SELECT username, email FROM users WHERE id = ?", (user['id'],))
        updated_user = c.fetchone()
        conn.close()
        
        assert updated_user is not None, "El usuario debería existir"
        assert updated_user[0] == 'updateduser', "El nombre de usuario debería haberse actualizado"
        assert updated_user[1] == 'updated@example.com', "El email debería haberse actualizado"
        
def test_song_api(client, test_db, app_context):
    """Prueba la funcionalidad de búsqueda de canciones"""
    # Login como usuario de prueba y configurar la sesión
    user = verify_user('testuser', 'testpass')
    assert user is not None, "El usuario debería existir"
    
    with client.session_transaction() as sess:
        sess['user_id'] = user['id']
        sess['username'] = user['username']
    
    # Agregar algunas canciones para buscar
    songs = [
        ("Test Song 1", "Artist 1", "http://example.com/1.mp3"),
        ("Another Song", "Artist 2", "http://example.com/2.mp3"),
        ("Test Different", "Artist 3", "http://example.com/3.mp3")
    ]
    
    # Agregar canciones a la base de datos
    for name, artist, url in songs:
        song_id = add_song(name, artist, url, user['id'])
        assert song_id is not None, f"Debería poder agregar la canción {name}"
    
    # Verificar que las canciones se agregaron
    response = client.get('/api/songs')
    assert response.status_code == 200, "Debería poder obtener las canciones"
    songs_list = response.get_json()
    assert len(songs_list) == 3, "Deberían haberse agregado 3 canciones"

    # Probar búsqueda por nombre
    response = client.post('/api/search', 
                         json={'search_term': 'Test'},
                         content_type='application/json')
    assert response.status_code == 200, "Debería poder buscar canciones"
    results = response.get_json()
    test_songs = [s for s in results if 'Test' in s['name']]
    assert len(test_songs) == 2, "Debería encontrar 2 canciones con 'Test'"

    # Probar búsqueda por artista
    response = client.post('/api/search',
                         json={'search_term': 'Artist 2'},
                         content_type='application/json')
    assert response.status_code == 200, "Debería poder buscar por artista"
    results = response.get_json()
    artist_songs = [s for s in results if s['artist'] == 'Artist 2']
    assert len(artist_songs) == 1, "Debería encontrar 1 canción del artista"

def test_admin_functions(client, test_db, app_context):
    """Prueba las funciones del panel de administración"""
    # Asegurarse que el admin existe y tiene el rol correcto
    with app.app_context():
        # Inicializar la base de datos y crear el admin
        init_db()
        # Verificar que existe el admin y configurar la sesión
        admin = verify_user('admin', 'admin123')
        assert admin is not None, "El usuario admin debería existir"
        assert admin['role'] == 'admin', "El usuario admin debería tener rol de administrador"
    
        with client.session_transaction() as sess:
            sess['user_id'] = admin['id']
            sess['username'] = admin['username']
            sess['user_role'] = 'admin'
    
        # Crear un usuario de prueba para eliminar
        success = add_user('testuser2', 'testpass', 'test2@example.com', role='user')
        assert success, "Debería poder crear un usuario de prueba"
    
        # Verificar acceso al panel de administración
        response = client.get('/admin')
        assert response.status_code == 200, "Debería poder acceder al panel de admin"
        assert b'admin' in response.data, "Debería mostrar el usuario admin"
        assert b'testuser2' in response.data, "Debería mostrar el usuario de prueba"

        # Obtener el ID del usuario de prueba
        db_path = app.config.get('DATABASE', 'music.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", ('testuser2',))
        user_id = c.fetchone()[0]
        conn.close()

        # Eliminar el usuario de prueba
        response = client.post('/admin/delete_user',
                             json={'userId': user_id},
                             content_type='application/json')
        assert response.status_code == 200, "Debería poder eliminar el usuario"
        result = response.get_json()
        assert result['success'] == True, "La operación debería ser exitosa"

        # Verificar que el usuario fue eliminado
        response = client.get('/admin')
        assert response.status_code == 200, "Debería poder acceder al panel de admin"
        assert b'testuser2' not in response.data, "El usuario eliminado no debería aparecer"

        # Verificar que el usuario realmente se eliminó de la base de datos
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users WHERE username = ?", ('testuser2',))
        count = c.fetchone()[0]
        conn.close()
        assert count == 0, "El usuario debería haberse eliminado de la base de datos"
