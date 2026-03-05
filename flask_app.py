from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename
from slugify import slugify
from PIL import Image
import zipfile
import sqlite3
import datetime
import os
import shutil

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Homepage: show all uploaded games
@app.route('/')
def homepage():
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('SELECT title, slug, description, thumbnail FROM games ORDER BY upload_date DESC')
    games = c.fetchall()
    conn.close()
    return render_template('index.html', games=games)

# Upload page: form for uploading new game
@app.route('/upload')
def upload_page():
    return render_template('upload.html')

# Submit route: handles form submission
@app.route('/submit', methods=['POST'])
def submit_game():
    title = request.form['title']
    description = request.form['description']
    thumbnail = request.files['thumbnail']
    zip_file = request.files['zipfile']

    slug = slugify(title)
    game_folder = os.path.join('static/games', slug)
    thumbnail_path = os.path.join('static/thumbnails', f'{slug}.jpg')

    os.makedirs(game_folder, exist_ok=True)

    # Save thumbnail
    thumbnail.save(thumbnail_path)

    # Save and extract zip
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(zip_file.filename))
    zip_file.save(zip_path)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(game_folder)
    os.remove(zip_path)

    # Save metadata to database
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('''
        INSERT INTO games (title, slug, description, thumbnail, game_path, upload_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (title, slug, description, thumbnail_path, game_folder, datetime.datetime.now()))
    conn.commit()
    conn.close()

    return redirect('/')

# Play route: embed Unity game
@app.route('/play/<slug>')
def play_game(slug):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('SELECT title FROM games WHERE slug = ?', (slug,))
    game = c.fetchone()
    conn.close()

    if game:
        title = game[0]
        game_path = f'/static/games/{slug}'
        return render_template('play.html', title=title, game_path=game_path)
    else:
        return "Game not found", 404


# Delete route: remove a game
@app.route('/delete/<slug>', methods=['POST'])
def delete_game(slug):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('SELECT thumbnail, game_path FROM games WHERE slug = ?', (slug,))
    game = c.fetchone()

    if game:
        thumbnail_path, game_folder = game
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
        if os.path.exists(game_folder):
            force_delete(game_folder)
        c.execute('DELETE FROM games WHERE slug = ?', (slug,))
        conn.commit()

    conn.close()
    return redirect('/')

def force_delete(path):
    import stat
    def onerror(func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    shutil.rmtree(path, onerror=onerror)


if __name__ == '__main__':
    app.run(debug=True)
