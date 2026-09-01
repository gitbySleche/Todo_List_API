from flask import Flask, request, jsonify 
from argon2 import PasswordHasher, exceptions
from datetime import datetime, timedelta
import secrets
import sqlite3


app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('registered_users.db')
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def validate_email(email):

    for character in email:
        if character == '@':
            index = email.index('@') 
            if email[index:index+10] == '@gmail.com' or email[index:index+12] == '@hotmail.com':
                return True
            break
    return False

def checkdb_for_email(email, cursor):

    cursor.execute('SELECT password, email FROM users WHERE email = :email', {'email': email})
    return cursor.fetchone()

@app.route('/register', methods=["POST"])
def register():

    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = PasswordHasher()

    try:
        if validate_email(data['email']) is False:
            return jsonify({'error': 'invalid email.'}), 400

        if checkdb_for_email(data['email'], cursor) is not None:
            return jsonify({'error': 'email already registered.'}), 400

        hashed_pass = ph.hash(data['password'])
        cursor.execute('INSERT into users(name, email, password) VALUES(:name, :email, :password)', {'name':data['name'], 'email':data['email'], 'password':hashed_pass})
        conn.commit()

    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 400

    else:
        token = secrets.token_urlsafe()
        new_id = cursor.lastrowid
        expires_at = datetime.now() + timedelta(hours=1)
        cursor.execute('INSERT into tokens(token, user_id, expires_at) VALUES(:token, :id, :expires_at)', {'token':token, 'user_id':new_id, 'expires_at':expires_at.isoformat()})
        conn.commit()
        return jsonify({'token':token}), 200

    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():

    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    email_check = checkdb_for_email(data['email'], cursor)
    ph = PasswordHasher()

    try:

        if validate_email(data['email']) is False:
            return jsonify({'error': 'invalid email.'}), 400

        if email_check is not None:

            stored_hash = email_check[0]
            submitted_pass = ph.hash(data['password'])

            try:
                ph.verify(stored_hash, submitted_pass)
                token = secrets.token_urlsafe()
                new_id = cursor.lastrowid
                expires_at = datetime.now() + timedelta(hours=1)
                cursor.execute('INSERT into tokens(token, user_id, expires_at) VALUES(:token, :id, :expires_at)', {'token':token, 'user_id':new_id, 'expires_at':expires_at.isoformat()}) #converts from datetime object to string
                conn.commit()
                return jsonify({'token': token}), 200

            except exceptions.VerifyMismatchError:
                return jsonify({'error': 'invalid password.'}), 400

            finally:
                conn.close()

        else: 
            return jsonify({'error': 'email not found.'}), 400

    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 400

    finally:
        conn.close()


@app.route('/todos', methods=['POST'])
def create_to_dos():

    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute('SELECT user_id, expires_at FROM tokens WHERE token = :token', {'token':data['token']})
        token = cursor.fetchone()

        if token is not None:

            token_expiry = datetime.fromisoformat(token[1])  #converts from string to datetime object

            if datetime.now() > token_expiry:
                return jsonify({'message':'Unauthorized'}), 401

            else:
                cursor.execute('INSERT into todo(user_id, text, description) VALUES(:user_id, :text, :description)', {'user_id':token[0], 'text':data['title'], 'description':data['description']})
                conn.commit()
                todo_query = cursor.execute('SELECT id, title, description FROM todo WHERE user_id = :user_id', {'user_id':token[0]})
                return jsonify({'id':todo_query[0], 'title':todo_query[1], 'description':todo_query[2]})

        else:
            return jsonify({'message':'Unauthorized'}), 401


    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 400
    
    finally:
        conn.close()

              
    
@app.route('todo/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):

    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
    
        cursor.execute('SELECT user_id FROM tokens WHERE token = :token', {'token':data['token']})
        token = cursor.fetchone()

        if token is not None: #check if token exists

            token_expiry = datetime.fromisoformat(token[1])  #converts from string to datetime object
            
            if datetime.now() > token_expiry:
                return jsonify({'message':'Unauthorized'}), 401

            else:
                cursor.execute('SELECT user_id FROM todo WHERE id = :id', {'id':todo_id})
                todo_to_update = cursor.fetchone

                if todo_to_update is not None: #check if the todo the user wants to change, exists

                    if token[0] == todo_to_update[0]: #check if the user has permission to change todo

                        cursor.execute('UPDATE todo SET title = :title, description = :description WHERE id = :id', {'title':data['title'], 'description':data['description'], 'id':todo_id})
                        conn.commit()
                        todo_query = cursor.execute('SELECT id, title, description FROM todo WHERE id = :id', {'id':todo_id})
                        return jsonify({'id':todo_query[0], 'title':todo_query[1], 'description':todo_query[2]})

                    else:
                        return jsonify({'message':'Forbidden'}), 403
                else:
                    return jsonify({'error':'Todo doesn\'t exist'}), 400
        else:
            return jsonify({'message':'Unauthorized'}), 401


    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 400
        
    finally:
        conn.close()


@app.route('todo/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):

    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute('SELECT user_id FROM tokens WHERE token = :token', {'token':data['token']})
        token = cursor.fetchone()
    
        if token is not None: 
    
            token_expiry = datetime.fromisoformat(token[1])  
                
            if datetime.now() > token_expiry:
                return jsonify({'message':'Unauthorized'}), 401

            else:
                cursor.execute('DELETE FROM todo WHERE rowid = :todo_id', {'todo_id':todo_id})
                conn.commit()
                return '', 204

        else:
            return jsonify({'message':'Unauthorized'}), 401


    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 400
            
    finally:
        conn.close()


@app.route('todo/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):

    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute('SELECT user_id FROM tokens WHERE token = :token', {'token':data['token']})
        token = cursor.fetchone()
    
        if token is not None: 
    
            token_expiry = datetime.fromisoformat(token[1])  
                
            if datetime.now() > token_expiry:
                return jsonify({'message':'Unauthorized'}), 401

            else:
                

        else:
            return jsonify({'message':'Unauthorized'}), 401


    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 400
            
    finally:
        conn.close()




if __name__ == "__main__":
    app.run(debug=True)

