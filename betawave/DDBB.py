import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def init_db():
    conn = sqlite3.connect('music.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  email TEXT)''')
    
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
        hashed_pw = generate_password_hash(password)
        c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                 (username, hashed_pw, email))
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
    c.execute("SELECT id, name FROM songs WHERE user_id=?", (user_id,))
    songs = [{'id': row[0], 'name': row[1]} for row in c.fetchall()]
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
    c.execute('''SELECT s.id, s.name 
                 FROM songs s JOIN favorites f ON s.id = f.song_id 
                 WHERE f.user_id=?''', (user_id,))
    favorites = [{'id': row[0], 'name': row[1]} for row in c.fetchall()]
    conn.close()
    return favorites

def is_favorite(user_id, song_id):
    conn = sqlite3.connect('music.db')
    c = conn.cursor()
    c.execute("SELECT 1 FROM favorites WHERE user_id=? AND song_id=?", (user_id, song_id))
    result = c.fetchone() is not None
    conn.close()
    return result