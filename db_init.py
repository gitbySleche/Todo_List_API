import sqlite3 

con = sqlite3.connect('registered_users.db')
cursor = con.cursor()

cursor.execute('CREATE TABLE IF NOT EXISTS users(name TEXT, email TEXT, password TEXT)')
con.commit()
con.close()