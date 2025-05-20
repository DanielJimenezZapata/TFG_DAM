from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, flash
from functools import wraps
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import yt_dlp
import tempfile
import os
import traceback

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_super_segura'
app.config['STATIC_FOLDER'] = 'static'

# Database Functions
def init_db():
    conn = sqlite3.connect('music.db')
    c = conn.cursor()
    
    # Crear tabla users si no existe
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT
    )''')
      # Verificar si existe la columna created_at
    c.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in c.fetchall()]
    if 'created_at' not in columns:
        # Añadir columna created_at
        c.execute("ALTER TABLE users ADD COLUMN created_at DATETIME")
        # Actualizar registros existentes con la fecha actual
        from datetime import datetime
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("UPDATE users SET created_at = ? WHERE created_at IS NULL", (current_time,))
    
    c.execute('''CREATE TABLE IF NOT EXISTS songs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  url TEXT NOT NULL,
                  user_id INTEGER NOT NULL,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS favorites
                 (user_id INTEGER NOT NULL,
                  song_id INTEGER NOT NULL,
                  PRIMARY KEY (user_id, song_id),
                  FOREIGN KEY(user_id) REFERENCES users(id),
                  FOREIGN KEY(song_id) REFERENCES songs(id))''')
    
    conn.commit()
    conn.close()

def add_user(username, password, email=None):
    conn = sqlite3.connect('music.db')
    c = conn.cursor()
    try:
        from datetime import datetime
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        hashed_pw = generate_password_hash(password)
        c.execute("INSERT INTO users (username, password, email, created_at) VALUES (?, ?, ?, ?)",
                 (username, hashed_pw, email, current_time))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect('music.db')
    c = conn.cursor()
    c.execute("SELECT id, username, password FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    if user and check_password_hash(user[2], password):
        return {'id': user[0], 'username': user[1]}
    return None

def add_song(name, url, user_id):
    conn = sqlite3.connect('music.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO songs (name, url, user_id) VALUES (?, ?, ?)",
                 (name, url, user_id))
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_songs(user_id):
    conn = sqlite3.connect('music.db')
    c = conn.cursor()
    c.execute("SELECT id, name, url FROM songs WHERE user_id=?", (user_id,))
    songs = [{'id': row[0], 'name': row[1], 'url': row[2]} for row in c.fetchall()]
    conn.close()
    return songs

def search_songs(user_id, search_term):
    conn = sqlite3.connect('music.db')
    c = conn.cursor()
    c.execute("SELECT id, name, url FROM songs WHERE user_id=? AND LOWER(name) LIKE ?", 
             (user_id, f'%{search_term.lower()}%'))
    songs = [{'id': row[0], 'name': row[1], 'url': row[2]} for row in c.fetchall()]
    conn.close()
    return songs

def get_song_url(song_id, user_id):
    conn = sqlite3.connect('music.db')
    c = conn.cursor()
    c.execute("SELECT url FROM songs WHERE id=? AND user_id=?", (song_id, user_id))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def delete_song(song_id, user_id):
    conn = sqlite3.connect('music.db')
    c = conn.cursor()
    c.execute("DELETE FROM songs WHERE id=? AND user_id=?", (song_id, user_id))
    c.execute("DELETE FROM favorites WHERE song_id=?", (song_id,))
    conn.commit()
    rows_affected = c.rowcount
    conn.close()
    return rows_affected > 0

def add_favorite(user_id, song_id):
    conn = sqlite3.connect('music.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO favorites VALUES (?, ?)", (user_id, song_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def remove_favorite(user_id, song_id):
    conn = sqlite3.connect('music.db')
    c = conn.cursor()
    c.execute("DELETE FROM favorites WHERE user_id=? AND song_id=?", (user_id, song_id))
    conn.commit()
    rows_affected = c.rowcount
    conn.close()
    return rows_affected > 0

def get_favorites(user_id):
    conn = sqlite3.connect('music.db')
    c = conn.cursor()
    c.execute('''SELECT s.id, s.name, s.url 
                 FROM songs s JOIN favorites f ON s.id = f.song_id 
                 WHERE f.user_id=?''', (user_id,))
    favorites = [{'id': row[0], 'name': row[1], 'url': row[2]} for row in c.fetchall()]
    conn.close()
    return favorites

def is_favorite(user_id, song_id):
    conn = sqlite3.connect('music.db')
    c = conn.cursor()
    c.execute("SELECT 1 FROM favorites WHERE user_id=? AND song_id=?", (user_id, song_id))
    result = c.fetchone() is not None
    conn.close()
    return result

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
          # Obtener información del usuario actual
        conn = sqlite3.connect('music.db')
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
    conn = sqlite3.connect('music.db')
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
            'format': 'bestaudio/best',
            'quiet': True,
            'extract_flat': True,
            'force_ipv4': True,
            'socket_timeout': 10
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(song_url, download=False)
            return jsonify({
                'audio_stream_url': info['url'],
                'song_id': song_id
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
        if delete_song(data.get('song_id'), session['user_id']):
            return jsonify({'success': True})
        return jsonify({'error': 'Canción no encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add_song', methods=['POST'])
@login_required
def add_song_route():
    try:
        data = request.json
        song_name = data.get('song_name')
        song_url = data.get('song_url')
        user_id = session['user_id']
        
        if not song_name or not song_url:
            return jsonify({'error': 'Nombre y URL son requeridos'}), 400
        
        if 'youtube.com' not in song_url and 'youtu.be' not in song_url:
            return jsonify({'error': 'Solo se aceptan URLs de YouTube'}), 400
            
        song_id = add_song(song_name, song_url, user_id)
        if song_id:
            new_song = {
                'id': song_id,
                'name': song_name,
                'url': song_url,
                'user_id': user_id
            }
            return jsonify({'success': True, 'song': new_song})
        return jsonify({'error': 'La canción ya existe'}), 400
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
        song_id = data.get('song_id')
        user_id = session['user_id']
        
        if is_favorite(user_id, song_id):
            remove_favorite(user_id, song_id)
            return jsonify({'is_favorite': False})
        else:
            if add_favorite(user_id, song_id):
                return jsonify({'is_favorite': True})
            return jsonify({'error': 'Canción no encontrada'}), 404
    except Exception as e:
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

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=8501)