from flask import Flask, request, jsonify 
from argon2 import PasswordHasher, exceptions
from datetime import datetime, timedelta
import secrets
import sqlite3


app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('todos.db')
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

    cursor.execute('SELECT password, email, id FROM users WHERE email = :email', {'email': email})
    return cursor.fetchone()

@app.route('/register', methods=["POST"])
def register():

    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = PasswordHasher()

    try:

        required_fields = ['name', 'email', 'password']

        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        elif validate_email(data['email']) is False:
            return jsonify({'error': 'invalid email.'}), 400

        elif checkdb_for_email(data['email'], cursor) is not None:
            return jsonify({'error': 'email already registered.'}), 400

        else:
            hashed_pass = ph.hash(data['password'])
            cursor.execute('INSERT into users(name, email, password) VALUES(:name, :email, :password)', {'name':data['name'], 'email':data['email'], 'password':hashed_pass})
            conn.commit()
        

    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 400

    else:
        token = secrets.token_urlsafe()
        new_id = cursor.lastrowid
        expires_at = datetime.now() + timedelta(hours=1)
        cursor.execute('INSERT into tokens(token, user_id, expires_at) VALUES(:token, :user_id, :expires_at)', {'token':token, 'user_id':new_id, 'expires_at':expires_at.isoformat()})
        conn.commit()
        return jsonify({'token':token}), 201

    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():

    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = PasswordHasher()

    try:

        required_fields = ['email', 'password']
        
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400    

        elif validate_email(data['email']) is False:
            return jsonify({'error': 'invalid email.'}), 400
        
        email_check = checkdb_for_email(data['email'], cursor)
        
        if email_check is not None:

            stored_hash = email_check[0]
            submitted_pass = data['password']

            try:
                ph.verify(stored_hash, submitted_pass)
                token = secrets.token_urlsafe()
                new_id = email_check[2]
                expires_at = datetime.now() + timedelta(hours=1)
                cursor.execute('INSERT into tokens(token, user_id, expires_at) VALUES(:token, :user_id, :expires_at)', {'token':token, 'user_id':new_id, 'expires_at':expires_at.isoformat()}) #converts from datetime object to string
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
    auth_header = request.headers.get('Authorization')
    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        required_fields = ['title', 'description']

        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        elif not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'message':'Unauthorized'}), 401

        token_submitted = auth_header.split(' ')[1]

        cursor.execute('SELECT user_id, expires_at FROM tokens WHERE token = :token', {'token':token_submitted})
        token = cursor.fetchone()

        if token is not None:

            token_expiry = datetime.fromisoformat(token[1])  #converts from string to datetime object

            if datetime.now() > token_expiry:
                return jsonify({'message':'Unauthorized'}), 401

            else:
                cursor.execute('INSERT into todo(user_id, title, description) VALUES(:user_id, :title, :description)', {'user_id':token[0], 'title':data['title'], 'description':data['description']})
                conn.commit()
                cursor.execute('SELECT id, title, description FROM todo WHERE user_id = :user_id', {'user_id':token[0]})
                todo_query = cursor.fetchone()
                return jsonify({'id':todo_query[0], 'title':todo_query[1], 'description':todo_query[2]}), 201

        else:
            return jsonify({'message':'Unauthorized'}), 401


    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 400
    
    finally:
        conn.close()

              
    
@app.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):

    data = request.get_json()
    auth_header = request.headers.get('Authorization')
    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        required_fields = ['title', 'description']

        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        elif not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'message':'Unauthorized'}), 401

        token_submitted = auth_header.split(' ')[1]
    
        cursor.execute('SELECT user_id, expires_at FROM tokens WHERE token = :token', {'token':token_submitted})
        token = cursor.fetchone()

        if token is not None: #check if token exists

            token_expiry = datetime.fromisoformat(token[1])  #converts from string to datetime object
            
            if datetime.now() > token_expiry:
                return jsonify({'message':'Unauthorized'}), 401

            else:
                cursor.execute('SELECT user_id FROM todo WHERE id = :id', {'id':todo_id})
                todo_to_update = cursor.fetchone()

                if todo_to_update is not None: #check if the todo the user wants to change, exists

                    if token[0] == todo_to_update[0]: #check if the user has permission to change todo

                        cursor.execute('UPDATE todo SET title = :title, description = :description WHERE id = :id', {'title':data['title'], 'description':data['description'], 'id':todo_id})
                        conn.commit()
                        cursor.execute('SELECT id, title, description FROM todo WHERE id = :id', {'id':todo_id})
                        todo_query = cursor.fetchone()
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


@app.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):

    auth_header = request.headers.get('Authorization')
    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'message':'Unauthorized'}), 401

        token_submitted = auth_header.split(' ')[1]

        cursor.execute('SELECT user_id, expires_at FROM tokens WHERE token = :token', {'token':token_submitted})
        token = cursor.fetchone()
    
        if token is not None: 
    
            token_expiry = datetime.fromisoformat(token[1])  
                
            if datetime.now() > token_expiry:
                return jsonify({'message':'Unauthorized'}), 401

            else:

                cursor.execute('SELECT user_id FROM todo WHERE id = :id', {'id':todo_id})
                todo_to_delete = cursor.fetchone()
                
                if todo_to_delete is not None: 
                
                    if token[0] == todo_to_delete[0]: 

                        cursor.execute('DELETE FROM todo WHERE rowid = :todo_id', {'todo_id':todo_id})
                        conn.commit()
                        return '', 204

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


@app.route('/todos', methods=['GET'])
def get_todo():

    auth_header = request.headers.get('Authorization')
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=10, type=int)
    offset = (page - 1) * limit #how many rows to skip before to start returning results, i.e: in 200 rows, show the last 10 which is page=20, limit=10 (20-1)*10=190, skip the first 190 rows
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:

        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'message':'Unauthorized'}), 401

        token_submitted = auth_header.split(' ')[1]

        cursor.execute('SELECT user_id, expires_at FROM tokens WHERE token = :token', {'token':token_submitted})
        token = cursor.fetchone()
    
        if token is not None: 
    
            token_expiry = datetime.fromisoformat(token[1])  
                
            if datetime.now() > token_expiry:
                return jsonify({'message':'Unauthorized'}), 401

            else:
                
                cursor.execute('SELECT id, title, description FROM todo WHERE user_id = :user_id LIMIT :limit OFFSET :offset', {'user_id': token[0], 'limit': limit, 'offset': offset})
                rows = cursor.fetchall()
                todo_list = [dict(row) for row in rows]

                cursor.execute('SELECT COUNT(*) FROM todo WHERE user_id = :user_id', {'user_id': token[0]})
                total = cursor.fetchone()[0]

                return jsonify({'data': todo_list, 'page': page, 'limit': limit, 'total': total}), 200

        else:
            return jsonify({'message':'Unauthorized'}), 401


    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 400
            
    finally:
        conn.close()




if __name__ == "__main__":
    app.run(debug=True)

