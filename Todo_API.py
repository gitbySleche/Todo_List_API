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

@app.route('/register', methods=["POST"])
def register():

    data = request.get_json()
    con = sqlite3.connect('registered_users.db')
    cursor = con.cursor()
    ph = PasswordHasher()

    try:
        if validate_email(data['email']) is not True:
            return jsonify({'error': 'invalid email.'}), 400

        cursor.execute('SELECT * FROM users WHERE email = :email', {'email':data['email']})

        if cursor.fetchone() == data['email']:
            return jsonify({'error': 'email already registered.'}), 400

        hashed_pass = ph.hash(data['password'])
        cursor.execute('INSERT into users VALUES(:name, :email, :password)', {'name':data['name'], 'email':data['email'], 'password':hashed_pass})
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

    

    



    


    






if __name__ == "__main__":
    app.run(debug=True)

