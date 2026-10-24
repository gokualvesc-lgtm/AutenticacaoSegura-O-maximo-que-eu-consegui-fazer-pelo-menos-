import sqlite3

conn = sqlite3.connect("PassWords_reset.db")

cursor = conn.cursor()

cursor.execute("""
        CREATE TABLE IF NOT EXISTS passwords_reset (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        tentativas INTEGER NOT NULL,
        codigo TEXT NOT NULL
        )
""")

conn.commit()
conn.close()

