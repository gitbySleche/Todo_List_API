import sqlite3 

con = sqlite3.connect('registered_users.db')
cursor = con.cursor()

cursor.execute('CREATE TABLE IF NOT EXISTS users(name TEXT, email TEXT, password TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS todo(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, description TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS tokens(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, description TEXT)')
con.commit()
con.close()