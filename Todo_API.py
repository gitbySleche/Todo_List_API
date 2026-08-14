from flask import Flask, request, jsonify 
from argon2 import PasswordHasher
import secrets
import sqlite3

app = Flask(__name__)

def validate_email(email):

    for character in email:
        if character == '@':
            index = email.index('@') 
            if email[index:index+10] == '@gmail.com' or email[index:index+12] == '@hotmail.com':
                return True
            break
    return False

def checkdb_for_email(email, cursor):

    cursor.execute('SELECT rowid, email FROM users WHERE email = :email', {'email': email})
    return cursor.fetchone()

@app.route('/register', methods=["POST"])
def register():

    data = request.get_json()
    con = sqlite3.connect('registered_users.db')
    cursor = con.cursor()
    ph = PasswordHasher()

    try:
        if validate_email(data['email']) is False:
            return jsonify({'error': 'invalid email.'}), 400

        if checkdb_for_email(data['email'], cursor) is not None:
            return jsonify({'error': 'email already registered.'}), 400

        hashed_pass = ph.hash(data['password'])
        cursor.execute('INSERT into users(name, email, password) VALUES(:name, :email, :password)', {'name':data['name'], 'email':data['email'], 'password':hashed_pass})
        con.commit()

    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 400

    else:
        registration_token = secrets.token_urlsafe()
        return jsonify({'token':registration_token}), 200

    finally:
        con.close()

@app.route('/login', methods=['POST'])
def login():

    data = request.get_json()
    con = sqlite3.connect('registered_users.db')
    cursor = con.cursor()
    email_check = checkdb_for_email(data['email'], cursor)

    try:
        if email_check is not None:

            cursor.execute('SELECT rowid, password FROM users WHERE rowid= :rowid', {'rowid': email_check[0]})
            password = cursor.fetchone()[0]

            if password == data['password']:
                login_token = secrets.token_urlsafe()
                return jsonify({'token': login_token}), 200

            else:
                return jsonify({'error': 'invalid password.'}), 400

        else: 
            return jsonify({'error': 'email not found.'}), 400

    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 400

    finally:
        con.close()


@app.route('/todos', methods=['POST'])
def to_dos():

    data = request.get_json()
    con = sqlite3.connect('registered_users.db')
    cursor = con.cursor()

    try:

        if data['token'] ==  
    



    


    






if __name__ == "__main__":
    app.run(debug=True)

