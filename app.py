import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret')
DATABASE = os.environ.get('DATABASE_URL', 'wtm.db')


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS parties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            host_name TEXT NOT NULL,
            party_name TEXT NOT NULL,
            location TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    conn.commit()
    conn.close()


init_db()


def current_user():
    if 'user_id' in session:
        return {'id': session['user_id'], 'email': session.get('user')}
    return None


def get_upcoming_parties(limit=3):
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
        WHERE datetime(p.date || ' ' || p.time) >= datetime('now', 'localtime')
        ORDER BY datetime(p.date || ' ' || p.time)
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return parties

@app.route('/')
def index():
    upcoming = get_upcoming_parties(limit=3)
    return render_template('index.html', upcoming_parties=upcoming)

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


@app.route('/party/<int:party_id>')
def party_detail(party_id):
    conn = get_db_connection()
    party = conn.execute(
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
        WHERE p.id = ?
        """,
        (party_id,),
    ).fetchone()
    conn.close()
    if not party:
        return redirect(url_for('list_page'))
    return render_template('party_detail.html', party=party)

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


@app.route('/add', methods=['GET', 'POST'])
def add_party():
    user = current_user()
    if request.method == 'GET':
        return render_template('add.html', user=user)

    if not user:
        return redirect(url_for('login_page'))

    host_name = request.form.get('host_name')
    party_name = request.form.get('party_name')
    location = request.form.get('location')
    date = request.form.get('date')
    time = request.form.get('time')
    description = request.form.get('description', '')

    if not all([host_name, party_name, location, date, time]):
        return render_template('add.html', user=user, error="All fields except description are required.")

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
