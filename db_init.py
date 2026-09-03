import sqlite3 

con = sqlite3.connect('registered_users.db')
cursor = con.cursor()

cursor.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, email TEXT NOT NULL, password TEXT NOT NULL)')
cursor.execute('CREATE TABLE IF NOT EXISTS todo(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, title TEXT NOT NULL, description TEXT, FOREIGN KEY (user_id) REFERENCES users(id))')
cursor.execute('CREATE TABLE IF NOT EXISTS tokens(token TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires_at TIMESTAMP NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id))')
con.commit()
con.close()