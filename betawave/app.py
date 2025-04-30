from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, flash
from functools import wraps
from DDBB import init_db, add_user, verify_user
from DDBB import add_song, get_songs, get_song_url, delete_song
from DDBB import add_favorite, remove_favorite, get_favorites, is_favorite
import yt_dlp
import tempfile
import os
import traceback

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_super_segura'  # Cambiar en producción!
init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

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

def get_audio_stream_url(video_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'extract_flat': True,
        'force_ipv4': True,
        'socket_timeout': 10
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return info['url']
    except Exception as e:
        traceback.print_exc()
        raise Exception(f"No se pudo obtener el stream: {str(e)}")

@app.route('/api/songs', methods=['GET'])
@login_required
def get_songs_route():
    return jsonify(get_songs(session['user_id']))

@app.route('/api/play', methods=['POST'])
@login_required
def play_song():
    try:
        data = request.json
        song_id = data.get('song_id')
        song_url = get_song_url(song_id, session['user_id'])
        
        if not song_url:
            return jsonify({'error': 'Canción no encontrada'}), 404
        
        audio_stream_url = get_audio_stream_url(song_url)
        return jsonify({
            'audio_stream_url': audio_stream_url,
            'song_id': song_id
        })
    except Exception as e:
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
    data = request.json
    if delete_song(data.get('song_id'), session['user_id']):
        return jsonify({'success': True})
    return jsonify({'error': 'Canción no encontrada'}), 404

@app.route('/api/add_song', methods=['POST'])
@login_required
def add_song_route():
    data = request.json
    song_id = add_song(data.get('song_name'), data.get('song_url'), session['user_id'])
    if song_id:
        return jsonify({'success': True, 'song_id': song_id})
    return jsonify({'error': 'La canción ya existe'}), 400

@app.route('/api/favorites', methods=['GET'])
@login_required
def get_favorites_route():
    return jsonify(get_favorites(session['user_id']))

@app.route('/api/toggle_favorite', methods=['POST'])
@login_required
def toggle_favorite():
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

@app.route('/api/is_favorite', methods=['POST'])
@login_required
def check_favorite():
    data = request.json
    return jsonify({
        'is_favorite': is_favorite(session['user_id'], data.get('song_id'))
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8501)