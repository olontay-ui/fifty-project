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


@app.route('/party/<int:party_id>')
def party_detail(party_id):
    conn = get_db_connection()
    party = conn.execute(
        """
        SELECT p.id,
               p.user_id,
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


@app.route('/party/<int:party_id>/edit', methods=['GET', 'POST'])
def edit_party(party_id):
    user = current_user()
    if not user:
        return redirect(url_for('login_page'))

    conn = get_db_connection()
    party = conn.execute("SELECT * FROM parties WHERE id = ?", (party_id,)).fetchone()

    # Permission check - ensure that only creator can edit
    if not party or party['user_id'] != user['id']:
        conn.close()
        return redirect(url_for('party_detail', party_id=party_id))

    if request.method == 'POST':
        host_name = request.form.get('host_name')
        party_name = request.form.get('party_name')
        location = request.form.get('location')
        date = request.form.get('date')
        time = request.form.get('time')
        description = request.form.get('description')

        conn.execute(
            """
            UPDATE parties
            SET host_name = ?, party_name = ?, location = ?, date = ?, time = ?, description = ?
            WHERE id = ?
            """,
            (host_name, party_name, location, date, time, description, party_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('party_detail', party_id=party_id))

    conn.close()
    return render_template('edit_party.html', party=party, user=user)


@app.route('/party/<int:party_id>/delete', methods=['POST'])
def delete_party(party_id):
    user = current_user()
    if not user:
        return redirect(url_for('login_page'))

    conn = get_db_connection()
    party = conn.execute("SELECT * FROM parties WHERE id = ?", (party_id,)).fetchone()

    # Permission check: ensure only user who created can delete
    if party and party['user_id'] == user['id']:
        conn.execute("DELETE FROM parties WHERE id = ?", (party_id,))
        conn.commit()

    conn.close()
    return redirect(url_for('list_page'))

# Add this function after the init_db() function to create the wishlist table

def init_wishlist_table():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            party_id INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (party_id) REFERENCES parties(id) ON DELETE CASCADE,
            UNIQUE(user_id, party_id)
        );
        """
    )
    conn.commit()
    conn.close()

# Call this after init_db()
init_wishlist_table()


# Add this helper function to get user's wishlist party IDs
def get_user_wishlist_ids(user_id):
    """Returns a set of party IDs that are in the user's wishlist"""
    if not user_id:
        return set()
    
    conn = get_db_connection()
    wishlist_items = conn.execute(
        "SELECT party_id FROM wishlist WHERE user_id = ?",
        (user_id,)
    ).fetchall()
    conn.close()
    
    return {item['party_id'] for item in wishlist_items}


# Update your list_page route to include wishlist data
@app.route('/list')
def list_page():
    user = current_user()
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
    
    # Get user's wishlist IDs
    user_wishlist = get_user_wishlist_ids(user['id']) if user else set()
    
    return render_template('list.html', parties=parties, user=user, user_wishlist=user_wishlist)


# Add the wishlist page route
@app.route('/wishlist')
def wishlist_page():
    user = current_user()
    if not user:
        return redirect(url_for('login_page'))
    
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
               u.username AS created_by,
               w.added_at
        FROM wishlist w
        JOIN parties p ON w.party_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE w.user_id = ?
        ORDER BY w.added_at DESC
        """,
        (user['id'],)
    ).fetchall()
    conn.close()
    
    message = "You haven't added any parties to your wishlist yet." if not parties else None
    
    return render_template('wishlist.html', parties=parties, message=message, user=user)


# Add the toggle wishlist route (AJAX endpoint)
@app.route('/party/<int:party_id>/wishlist', methods=['POST'])
def toggle_wishlist(party_id):
    user = current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    
    # Check if party exists
    party = conn.execute("SELECT id FROM parties WHERE id = ?", (party_id,)).fetchone()
    if not party:
        conn.close()
        return jsonify({'error': 'Party not found'}), 404
    
    # Check if already in wishlist
    existing = conn.execute(
        "SELECT id FROM wishlist WHERE user_id = ? AND party_id = ?",
        (user['id'], party_id)
    ).fetchone()
    
    if existing:
        # Remove from wishlist
        conn.execute(
            "DELETE FROM wishlist WHERE user_id = ? AND party_id = ?",
            (user['id'], party_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'action': 'removed', 'party_id': party_id})
    else:
        # Add to wishlist
        conn.execute(
            "INSERT INTO wishlist (user_id, party_id) VALUES (?, ?)",
            (user['id'], party_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'action': 'added', 'party_id': party_id})
    

if __name__ == '__main__':
    app.run(debug=True)