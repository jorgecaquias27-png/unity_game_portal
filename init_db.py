import sqlite3

conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    slug TEXT UNIQUE,
    description TEXT,
    thumbnail TEXT,
    game_path TEXT,
    upload_date TEXT
)
''')

conn.commit()
conn.close()
