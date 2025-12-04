import os
import sqlite3
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret')
DATABASE = os.environ.get('DATABASE_URL', 'wtm.db')


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn



def current_user():
    if 'user_id' in session:
        return {'id': session['user_id'], 'email': session.get('user')}
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/list')
def list_page():
    conn = get_db_connection()
    parties = conn.execute(
        """
        SELECT p.id,
               p.party_name,
               p.location,
               p.date,
               p.time,
               p.description,
               p.host_name,
               p.created_at,
               u.username AS created_by
        FROM parties p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.date, p.time
        """
    ).fetchall()
    conn.close()
    return render_template('list.html', parties=parties)

@app.route('/feed')
def feed():
    return render_template('feed.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_submit():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return render_template('login.html', error="Email and password are required.")

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (email,)).fetchone()
    conn.close()

    if user and check_password_hash(user["hash"], password):
        session['user'] = email
        session['user_id'] = user["id"]
        return redirect(url_for('index'))

    return render_template('login.html', error="Invalid email or password.")

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_submit():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return render_template('register.html', error="Email and password are required.")

    conn = get_db_connection()
    existing = conn.execute("SELECT 1 FROM users WHERE username = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return render_template('register.html', error="An account with that email already exists.")

    hashed_password = generate_password_hash(password)
    cursor = conn.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (email, hashed_password))
    conn.commit()
    session['user'] = email
    session['user_id'] = cursor.lastrowid
    conn.close()

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/parties', methods=['POST'])
def add_party():
    user = current_user()
    if not user:
        return redirect(url_for('login_page'))

    host_name = request.form.get('host_name')
    party_name = request.form.get('party_name')
    location = request.form.get('location')
    date = request.form.get('date')
    time = request.form.get('time')
    description = request.form.get('description', '')

    if not all([host_name, party_name, location, date, time]):
        return redirect(url_for('list_page'))

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO parties (user_id, host_name, party_name, location, date, time, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user['id'], host_name, party_name, location, date, time, description),
    )
    conn.commit()
    conn.close()

    return redirect(url_for('list_page'))


if __name__ == '__main__':
    app.run(debug=True)
