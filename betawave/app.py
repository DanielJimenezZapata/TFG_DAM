from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, flash
from functools import wraps
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import yt_dlp
import tempfile
import os
import traceback
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'tu_clave_secreta_super_segura')

# Ensure data directory exists
data_dir = Path('data')
data_dir.mkdir(exist_ok=True)

# Database configuration
app.config['DATABASE'] = os.environ.get('DATABASE_PATH', str(data_dir / 'music.db'))
app.config['STATIC_FOLDER'] = 'static'

# Database Functions
def init_db():
    db_path = app.config['DATABASE']
    print(f"\n[init_db] Initializing database at: {db_path}")
    
    # Ensure parent directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        # Crear tabla users si no existe
        print("[init_db] Creating users table...")
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            created_at DATETIME
        )''')
        
        # Verificar si el usuario admin existe
        c.execute("SELECT username FROM users WHERE username = 'admin'")
        admin_exists = c.fetchone()
        print(f"[init_db] Admin exists: {admin_exists is not None}")
        
        # Si no existe el admin, crearlo
        if not admin_exists:
            from datetime import datetime
            admin_password = generate_password_hash('admin123')
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print("[init_db] Creating admin user...")
            c.execute("INSERT INTO users (username, password, role, created_at) VALUES (?, ?, 'admin', ?)",
                     ('admin', admin_password, current_time))

        # Verificar si existe la columna role
        c.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in c.fetchall()]    
        print(f"[init_db] Users table columns: {columns}")
        
        if 'role' not in columns:
            print("[init_db] Adding role column...")
            c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")    
        
        # Verificar si existe la columna created_at
        if 'created_at' not in columns:
            print("[init_db] Adding created_at column...")
            c.execute("ALTER TABLE users ADD COLUMN created_at DATETIME")
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute("UPDATE users SET created_at = ? WHERE created_at IS NULL", (current_time,))

        # Crear tabla songs si no existe
        print("[init_db] Creating songs table...")
        c.execute('''CREATE TABLE IF NOT EXISTS songs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT NOT NULL,
                      artist TEXT,
                      url TEXT NOT NULL,
                      user_id INTEGER NOT NULL,
                      FOREIGN KEY(user_id) REFERENCES users(id))''')
        
        print("[init_db] Creating favorites table...")
        c.execute('''CREATE TABLE IF NOT EXISTS favorites
                     (user_id INTEGER NOT NULL,
                      song_id INTEGER NOT NULL,
                      PRIMARY KEY (user_id, song_id),
                      FOREIGN KEY(user_id) REFERENCES users(id),
                      FOREIGN KEY(song_id) REFERENCES songs(id))''')
        
        print("[init_db] Creating user_config table...")
        c.execute('''CREATE TABLE IF NOT EXISTS user_config
                     (user_id INTEGER PRIMARY KEY,
                      dark_mode BOOLEAN DEFAULT 0,
                      default_volume INTEGER DEFAULT 50,
                      FOREIGN KEY(user_id) REFERENCES users(id))''')
        
        conn.commit()
        print("[init_db] Database initialization complete!")
        
        # Verify tables were created
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        print(f"[init_db] Tables in database: {[t[0] for t in tables]}")
        
    except sqlite3.Error as e:
        print(f"[init_db] SQLite error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def add_user(username, password, email=None, role='user'):
    print(f"[add_user] Adding user: username={username}, email={email}, role={role}")
    db_path = app.config.get('DATABASE', 'music.db')
    print(f"[add_user] Using database: {db_path}")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        from datetime import datetime
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        hashed_pw = generate_password_hash(password)
        c.execute("INSERT INTO users (username, password, email, role, created_at) VALUES (?, ?, ?, ?, ?)",
                 (username, hashed_pw, email, role, current_time))
        conn.commit()
        print("[add_user] User added successfully")
        return True
    except sqlite3.IntegrityError as e:
        print(f"[add_user] SQLite Integrity Error: {e}")
        return False
    except sqlite3.Error as e:
        print(f"[add_user] SQLite Error: {e}")
        return False
    finally:
        conn.close()

def verify_user(username, password):
    db_path = app.config.get('DATABASE', 'music.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id, username, password, role FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    if user and check_password_hash(user[2], password):
        return {'id': user[0], 'username': user[1], 'role': user[3]}
    return None

def add_song(name, artist, url, user_id):
    db_path = app.config.get('DATABASE', 'music.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO songs (name, artist, url, user_id) VALUES (?, ?, ?, ?)",
                 (name, artist, url, user_id))
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_songs(user_id):
    db_path = app.config.get('DATABASE', 'music.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id, name, artist, url FROM songs WHERE user_id=?", (user_id,))
    songs = [{'id': row[0], 'name': row[1], 'artist': row[2], 'url': row[3]} for row in c.fetchall()]
    conn.close()
    return songs

def search_songs(user_id, search_term):
    """
    Busca canciones por nombre o artista
    """
    db_path = app.config.get('DATABASE', 'music.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("""
            SELECT id, name, artist, url 
            FROM songs 
            WHERE user_id = ? AND (
                LOWER(name) LIKE ? OR 
                LOWER(artist) LIKE ?
            )
        """, (user_id, f'%{search_term.lower()}%', f'%{search_term.lower()}%'))
        
        songs = [
            {
                'id': row[0],
                'name': row[1],
                'artist': row[2],
                'url': row[3]
            }
            for row in c.fetchall()
        ]
        return songs
    finally:
        conn.close()

def get_song_url(song_id, user_id):
    db_path = app.config.get('DATABASE', 'music.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT url FROM songs WHERE id=? AND user_id=?", (song_id, user_id))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def delete_song(song_id, user_id):
    db_path = app.config.get('DATABASE', 'music.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        # Primero verificar que la canción existe y pertenece al usuario
        c.execute("SELECT 1 FROM songs WHERE id=? AND user_id=?", (song_id, user_id))
        if not c.fetchone():
            return False
            
        # Eliminar primero las referencias en favoritos
        c.execute("DELETE FROM favorites WHERE song_id=?", (song_id,))
        
        # Luego eliminar la canción
        c.execute("DELETE FROM songs WHERE id=? AND user_id=?", (song_id, user_id))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def add_favorite(user_id, song_id):
    db_path = app.config.get('DATABASE', 'music.db')
    print(f"[add_favorite] Adding to favorites in database: {db_path}")
    print(f"[add_favorite] user_id: {user_id}, song_id: {song_id}")
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        # First check if the favorite already exists
        c.execute("SELECT 1 FROM favorites WHERE user_id=? AND song_id=?", (user_id, song_id))
        if c.fetchone() is not None:
            print("[add_favorite] Favorite already exists")
            return True

        # Add the favorite
        c.execute("INSERT INTO favorites VALUES (?, ?)", (user_id, song_id))
        conn.commit()
        print("[add_favorite] Successfully added favorite")
        return True
    except sqlite3.IntegrityError as e:
        print(f"[add_favorite] SQL error: {e}")
        return False
    finally:
        conn.close()

def remove_favorite(user_id, song_id):
    db_path = app.config.get('DATABASE', 'music.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM favorites WHERE user_id=? AND song_id=?", (user_id, song_id))
    conn.commit()
    rows_affected = c.rowcount
    conn.close()
    return rows_affected > 0

def get_favorites(user_id):
    db_path = app.config.get('DATABASE', 'music.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''SELECT s.id, s.name, s.artist, s.url 
                 FROM songs s JOIN favorites f ON s.id = f.song_id 
                 WHERE f.user_id=?''', (user_id,))
    favorites = [{'id': row[0], 'name': row[1], 'artist': row[2], 'url': row[3]} for row in c.fetchall()]
    conn.close()
    return favorites

def is_favorite(user_id, song_id):
    db_path = app.config.get('DATABASE', 'music.db')
    print(f"[is_favorite] Checking favorites in database: {db_path}")
    print(f"[is_favorite] user_id: {user_id}, song_id: {song_id}")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT 1 FROM favorites WHERE user_id=? AND song_id=?", (user_id, song_id))
    result = c.fetchone() is not None
    print(f"[is_favorite] Found in favorites: {result}")
    # Debug: check actual records
    c.execute("SELECT * FROM favorites")
    all_favs = c.fetchall()
    print(f"[is_favorite] All favorites in DB: {all_favs}")
    conn.close()
    return result

def get_user_config(user_id):
    db_path = app.config.get('DATABASE', 'music.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT dark_mode, default_volume FROM user_config WHERE user_id=?", (user_id,))
    config = c.fetchone()
    conn.close()
    
    if config is None:
        # Return default values if no config exists
        return {'dark_mode': False, 'default_volume': 50}
    return {'dark_mode': bool(config[0]), 'default_volume': config[1]}

def save_user_config(user_id, dark_mode, default_volume):
    db_path = app.config.get('DATABASE', 'music.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("""INSERT OR REPLACE INTO user_config (user_id, dark_mode, default_volume) 
                     VALUES (?, ?, ?)""", (user_id, dark_mode, default_volume))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

# Decorator para rutas de admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_role' not in session or session['user_role'] != 'admin':
            flash('Acceso no autorizado', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Helper decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
@login_required
def index():
    return render_template('index.html', username=session.get('username'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_role'] = user['role']  # Guardar el rol del usuario en la sesión
            
            # Redirigir a panel de admin si es admin, sino a la página principal
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            
            next_url = request.args.get('next') or url_for('index')
            return redirect(next_url)
        flash('Usuario o contraseña incorrectos', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if add_user(username, password, email):
            flash('Registro exitoso! Por favor inicia sesión', 'success')
            return redirect(url_for('login'))
        flash('El usuario ya existe', 'error')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        repeat_password = request.form.get('repeat_password')        # Obtener información del usuario actual
        db_path = app.config.get('DATABASE', 'music.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT password, email FROM users WHERE id = ?", (session['user_id'],))
        user_data = c.fetchone()
        
        if not user_data:
            flash('Usuario no encontrado', 'error')
            conn.close()
            return redirect(url_for('logout'))
            
        if user_data:
            current_stored_password = user_data[0]
            
            # Verificar si se está intentando cambiar la contraseña
            if current_password and new_password:
                if not check_password_hash(current_stored_password, current_password):
                    flash('La contraseña actual es incorrecta', 'error')
                    return redirect(url_for('profile'))

                # Verificar que las contraseñas nuevas coincidan
                if new_password != repeat_password:
                    flash('Las contraseñas nuevas no coinciden', 'error')
                    return redirect(url_for('profile'))
                
                # Actualizar contraseña
                new_password_hash = generate_password_hash(new_password)
                c.execute("UPDATE users SET password = ? WHERE id = ?", 
                         (new_password_hash, session['user_id']))
            
            # Actualizar email y username
            c.execute("UPDATE users SET email = ?, username = ? WHERE id = ?", 
                     (email, username, session['user_id']))
            conn.commit()
            
            # Actualizar el nombre de usuario en la sesión
            session['username'] = username
            
            flash('Perfil actualizado correctamente', 'success')
        conn.close()
        return redirect(url_for('profile'))
    
    # Obtener información del usuario y estadísticas
    db_path = app.config.get('DATABASE', 'music.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Obtener datos del usuario
    c.execute("SELECT username, email FROM users WHERE id = ?", (session['user_id'],))
    user_data = c.fetchone()
    if not user_data:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('logout'))
        
    user = {'username': user_data[0], 'email': user_data[1] if user_data[1] else ''}
    
    # Obtener estadísticas
    c.execute("SELECT COUNT(*) FROM songs WHERE user_id = ?", (session['user_id'],))
    songs_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM favorites WHERE user_id = ?", (session['user_id'],))
    favorites_count = c.fetchone()[0]
      # Obtener fecha de registro y calcular días
    c.execute("SELECT created_at FROM users WHERE id = ?", (session['user_id'],))
    created_at = c.fetchone()[0]
    if created_at:
        from datetime import datetime
        created_date = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
        days_registered = (datetime.now() - created_date).days
    else:
        days_registered = 0
    
    conn.close()
    
    stats = {
        'songs_count': songs_count,
        'favorites_count': favorites_count,
        'days_registered': days_registered
    }
    
    return render_template('profile.html', user=user, stats=stats)

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    db_path = app.config.get('DATABASE', 'music.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Obtener todos los usuarios
    c.execute("""
        SELECT id, username, email, created_at, role 
        FROM users 
        ORDER BY created_at DESC
    """)
    users = [
        {
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'created_at': row[3],
            'role': row[4]
        }
        for row in c.fetchall()
    ]
    
    conn.close()
    return render_template('admin.html', users=users)



@app.route('/admin/delete_user', methods=['POST'])
@login_required
@admin_required
def admin_delete_user():
    try:
        data = request.get_json()
        user_id = data.get('userId')
        
        db_path = app.config.get('DATABASE', 'music.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Verificar que no sea un admin
        c.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        if user and user[0] == 'admin':
            return jsonify({'success': False, 'error': 'No se puede eliminar un administrador'})
        
        # Eliminar primero los registros relacionados
        c.execute("DELETE FROM favorites WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM songs WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM user_config WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error deleting user: {e}")
        return jsonify({'success': False, 'error': str(e)})

# API Endpoints
@app.route('/api/songs', methods=['GET'])
@login_required
def get_songs_route():
    try:
        songs = get_songs(session['user_id'])
        return jsonify(songs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
@login_required
def search_songs_route():
    try:
        data = request.json
        search_term = data.get('search_term', '')
        user_id = session['user_id']
        songs = search_songs(user_id, search_term)
        return jsonify(songs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/play', methods=['POST'])
@login_required
def play_song():
    try:
        data = request.json
        song_id = data.get('song_id')
        song_url = get_song_url(song_id, session['user_id'])
        
        if not song_url:
            return jsonify({'error': 'Canción no encontrada'}), 404
        ydl_opts = {
            'format': 'bestaudio',  # Solo busca formatos de audio
            'quiet': True,
            'extract_flat': True,
            'force_ipv4': True,
            'socket_timeout': 5,  # Reducir timeout a 5 segundos
            'nocheckcertificate': True,  # Evitar chequeos de certificados
            'prefer_insecure': True,  # Preferir conexiones más rápidas aunque sean menos seguras
            'geo_bypass': True  # Evitar restricciones geográficas
        }          # Primero obtener la información de la canción de nuestra base de datos
        db_path = app.config.get('DATABASE', 'music.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name, artist FROM songs WHERE id=? AND user_id=?", (song_id, session['user_id']))
        song_info = c.fetchone()
        conn.close()

        if not song_info:
            return jsonify({'error': 'Canción no encontrada'}), 404

        song_name, artist = song_info

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(song_url, download=False)
            return jsonify({
                'audio_stream_url': info['url'],
                'song_id': song_id,
                'title': song_name,
                'artist': artist
            })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e), 'fallback_url': song_url}), 500

@app.route('/api/download', methods=['POST'])
@login_required
def download_song():
    try:
        data = request.json
        song_id = data.get('song_id')
        format_type = data.get('format', 'mp3')
        song_url = get_song_url(song_id, session['user_id'])
        
        if not song_url:
            return jsonify({'error': 'Canción no encontrada'}), 404
        
        temp_dir = tempfile.mkdtemp()
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format_type,
                'preferredquality': '192',
            }]
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(song_url, download=True)
            filepath = ydl.prepare_filename(info).replace('.webm', f'.{format_type}').replace('.m4a', f'.{format_type}')
            return send_file(filepath, as_attachment=True, download_name=f"{info['title']}.{format_type}")
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete', methods=['POST'])
@login_required
def delete_song_route():
    try:
        data = request.json
        if not data or 'song_id' not in data:
            return jsonify({'success': False, 'error': 'ID de canción no proporcionado'}), 400
            
        song_id = data.get('song_id')
        if delete_song(song_id, session['user_id']):
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Canción no encontrada o no tienes permiso para eliminarla'}), 404
    except Exception as e:
        print(f"Error deleting song: {str(e)}")
        return jsonify({'success': False, 'error': 'Error al eliminar la canción'}), 500

@app.route('/api/add_song', methods=['POST'])
@login_required
def add_song_route():    
    try:
        data = request.json
        song_url = data.get('song_url')
        user_id = session['user_id']
        
        if not song_url:
            return jsonify({'error': 'URL es requerida'}), 400
        
        if 'youtube.com' not in song_url and 'youtu.be' not in song_url:
            return jsonify({'error': 'Solo se aceptan URLs de YouTube'}), 400
            
        # Obtener el título del video usando yt-dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',  # Extracción más rápida de metadatos
            'force_ipv4': True,
            'socket_timeout': 5,
            'nocheckcertificate': True,
            'prefer_insecure': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:            
            try:
                info = ydl.extract_info(song_url, download=False)
                song_name = info.get('title', '')
                if not song_name:
                    return jsonify({'error': 'No se pudo obtener el título del video'}), 400
                  # Intentar obtener el artista del video de diferentes formas
                artist = (
                    info.get('artist', '') or           # Metadatos del artista
                    info.get('creator', '') or          # Creador del video
                    info.get('uploader', '') or         # Quien subió el video
                    info.get('channel', '')             # Nombre del canal
                )
                
                # Si no se encontró el artista, intentar extraerlo del título
                if not artist and ' - ' in song_name:
                    # Formatos comunes: "Artista - Canción", "Artista - Topic - Canción"
                    parts = song_name.split(' - ')
                    artist = parts[0].strip()
                    # Si hay "Topic" en el nombre del artista, usar solo la primera parte
                    if 'topic' in artist.lower():
                        artist = artist.split('Topic')[0].strip()
                
                # Si aún no hay artista, intentar usar el nombre del canal sin "- Topic"
                if not artist:
                    channel = info.get('channel', '')
                    if channel:
                        if ' - Topic' in channel:
                            artist = channel.replace(' - Topic', '').strip()
                        else:
                            artist = channel
                
                # Si todo lo anterior falló, usar "Artista Desconocido"
                if not artist:
                    artist = 'Artista Desconocido'
                    
                song_id = add_song(song_name, artist, song_url, user_id)
                if song_id:
                    new_song = {
                        'id': song_id,
                        'name': song_name,
                        'artist': artist,
                        'url': song_url,
                        'user_id': user_id
                    }                    
                    return jsonify({'success': True, 'song': new_song})
                return jsonify({'error': 'La canción ya existe'}), 400
            except Exception as e:
                return jsonify({'error': 'Error al procesar el video: ' + str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/favorites', methods=['GET'])
@login_required
def get_favorites_route():
    try:
        favorites = get_favorites(session['user_id'])
        return jsonify(favorites)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/toggle_favorite', methods=['POST'])
@login_required
def toggle_favorite():
    try:
        data = request.json
        if not data or 'song_id' not in data:
            print("[toggle_favorite] No song_id in request")
            return jsonify({'error': 'song_id es requerido'}), 400
            
        song_id = data.get('song_id')
        user_id = session['user_id']
        print(f"[toggle_favorite] song_id: {song_id}, user_id: {user_id}")
        
        # First verify the song exists
        db_path = app.config.get('DATABASE', 'music.db')
        print(f"[toggle_favorite] Using database: {db_path}")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT 1 FROM songs WHERE id=?", (song_id,))
        song_exists = c.fetchone() is not None
        conn.close()
        
        if not song_exists:
            print("[toggle_favorite] Song not found")
            return jsonify({'error': 'Canción no encontrada'}), 404
        
        print("[toggle_favorite] Song exists, checking current favorite status")
        # Check current favorite status
        current_status = is_favorite(user_id, song_id)
        print(f"[toggle_favorite] Current favorite status: {current_status}")
        
        # Toggle the status
        if current_status:
            print("[toggle_favorite] Removing from favorites")
            success = remove_favorite(user_id, song_id)
        else:
            print("[toggle_favorite] Adding to favorites")
            success = add_favorite(user_id, song_id)
            
        if not success:
            print("[toggle_favorite] Error updating favorites")
            return jsonify({'error': 'Error al actualizar favoritos'}), 500
            
        new_status = not current_status
        print(f"[toggle_favorite] Operation successful, new status: {new_status}")
        return jsonify({'is_favorite': new_status})
    except Exception as e:
        print(f"[toggle_favorite] Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/is_favorite', methods=['POST'])
@login_required
def is_favorite_route():
    try:
        data = request.json
        song_id = data.get('song_id')
        user_id = session['user_id']
        result = is_favorite(user_id, song_id)
        return jsonify({'is_favorite': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/config')
@login_required
def config():
    user_config = get_user_config(session['user_id'])
    return render_template('config.html', 
                         username=session.get('username'),
                         email=session.get('email'),
                         config=user_config)

@app.route('/save_config', methods=['POST'])
def save_config():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    try:
        data = request.get_json()
        dark_mode = data.get('darkMode', False)
        default_volume = data.get('defaultVolume', 50)
        
        success = save_user_config(session['user_id'], dark_mode, default_volume)
        return jsonify({'success': success})
    except Exception as e:
        print(f"Error saving config: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'error')
        return redirect(url_for('login'))

    from DDBB import delete_user
    
    # Get the current password from the form
    current_password = request.form.get('current_password')
    
    # Verify the password before deletion
    conn = sqlite3.connect('music.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE id=?", (session['user_id'],))
    user = c.fetchone()
    conn.close()

    if not user or not check_password_hash(user[0], current_password):
        flash('Contraseña incorrecta. Por favor, inténtalo de nuevo.', 'error')
        return redirect(url_for('profile'))

    # Delete the account
    if delete_user(session['user_id']):
        session.clear()
        flash('Tu cuenta ha sido eliminada correctamente.', 'success')
        return redirect(url_for('login'))
    else:
        flash('Ha ocurrido un error al eliminar la cuenta. Por favor, inténtalo de nuevo.', 'error')
        return redirect(url_for('profile'))

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=8501)