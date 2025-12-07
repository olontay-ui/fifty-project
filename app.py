import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename #S

# Implement Flask and our database wtm.db
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret')
DATABASE = os.environ.get('DATABASE_URL', 'wtm.db')

# Configure some of the file uploads - s
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size 

# Create uploads directory if it doesn't exist - s 
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'posts'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'parties'), exist_ok=True)

# Helper function to check allowed file types - s
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Connect to wtm.db
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# This creates our "parties" table for this database
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
    conn.close()   # Closes the query after commiting


init_db()

# Keeps the current user in session
def current_user():
    if 'user_id' in session:
        return {'id': session['user_id'], 'email': session.get('user')}
    return None


# Shows upcoming parties on the homescreen of the front page
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


# Shows the upcoming parties
@app.route('/')
def index():
    upcoming = get_upcoming_parties(limit=3)
    return render_template('index.html', upcoming_parties=upcoming)


# Allows a user to add a party and party details
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
    conn.close()   # Party added to wtm.db
    if not party:
        return redirect(url_for('list_page'))
    return render_template('party_detail.html', party=party) 


# WTM Harvard's "About" page
@app.route('/about')
def about():
    return render_template('about.html')


# Creates the login-page
@app.route('/login')
def login_page():
    return render_template('login.html')


# Allows user to log into their account
@app.route('/login', methods=['POST'])
def login_submit():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return render_template('login.html', error="Email and password are required.")  # Ensures email and password are used for login

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (email,)).fetchone()
    conn.close()

    if user and check_password_hash(user["hash"], password):
        session['user'] = email
        session['user_id'] = user["id"]
        session['username'] = user["display_name"]  # Stores the username in the user's session
        return redirect(url_for('index'))

    return render_template('login.html', error="Invalid email or password.")


# Account registration page
@app.route('/register')
def register_page():
    return render_template('register.html')


# Register a new user on the website
@app.route('/register', methods=['POST'])
def register_submit():
    email = request.form.get('email')  # Asks for email
    password = request.form.get('password')  # Asks for password
    username = request.form.get('username')  # Asks for username

    # Valide the three fields
    if not email or not password or not username:
        return render_template('register.html', error="Email, username, and password are required.")

    # Vaidate username
    if len(username) < 3 or len(username) > 20:
        return render_template('register.html', error="Username must be between 3 and 20 characters.")
    
    if not username.replace('_', '').isalnum():
        return render_template('register.html', error="Username can only contain letters, numbers, and underscores.")

    conn = get_db_connection()
    
    # See if email already exists
    existing = conn.execute("SELECT 1 FROM users WHERE username = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return render_template('register.html', error="An account with that email already exists.")
    
    # See if username already exists
    existing_username = conn.execute("SELECT 1 FROM users WHERE display_name = ?", (username,)).fetchone()
    if existing_username:
        conn.close()
        return render_template('register.html', error="That username is already taken. Please choose another.")

    hashed_password = generate_password_hash(password)
    
    # Allows username to be diplayed instead of email
    cursor = conn.execute(
        "INSERT INTO users (username, hash, display_name) VALUES (?, ?, ?)", 
        (email, hashed_password, username)
    )
    conn.commit()
    session['user'] = email
    session['user_id'] = cursor.lastrowid  # Adds user's information to wtm.db
    session['username'] = username  
    conn.close()

    return redirect(url_for('index'))


# Allows user to log out
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))

# This is the Harvard Square location coordinates for geocoding - S
HARVARD_SQUARE_LOCATIONS = {
    'harvard square': (42.3736, -71.1190),
    'harvard yard': (42.3744, -71.1169),
    'widener library': (42.3744, -71.1167),
    'memorial hall': (42.3759, -71.1149),
    'science center': (42.3764, -71.1173),
    'annenberg': (42.3762, -71.1150),
    'lowell house': (42.3708, -71.1223),
    'adams house': (42.3717, -71.1211),
    'quincy house': (42.3719, -71.1205),
    'leverett house': (42.3716, -71.1194),
    'mather house': (42.3697, -71.1142),
    'dunster house': (42.3691, -71.1184),
    'eliot house': (42.3707, -71.1218),
    'kirkland house': (42.3721, -71.1230),
    'winthrop house': (42.3715, -71.1203),
    'pforzheimer house': (42.3824, -71.1246),
    'cabot house': (42.3818, -71.1252),
    'currier house': (42.3818, -71.1251),
}

def geocode_location(location):
    """Simple geocoding for Harvard locations"""
    location_lower = location.lower().strip()
    for key, coords in HARVARD_SQUARE_LOCATIONS.items():
        if key in location_lower:
            return coords
    # Default to Harvard Square if location not found
    return (42.3736, -71.1190)


# Allows user to add party and party details
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
    
    # This is the Security Feature to verify host name matches users display name - S

    conn = get_db_connection()
    #S 
    user_data = conn.execute("SELECT display_name FROM users WHERE id = ?", (user['id'],)).fetchone()
    
    if user_data['display_name'].lower() != host_name.lower():
        conn.close()
        return render_template('add.html', user=user, 
                             error=f"Host name must match your username ({user_data['display_name']}) to verify you are the actual host.")
    
    # Handle the flyer upload - S
    flyer_path = None 
    if 'flyer' in request.files:
        file = request.files['flyer']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Create unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'parties', filename)
            file.save(filepath)
            flyer_path = f'uploads/parties/{filename}'
    
    # Geocode location to get coordinates - S
    latitude, longitude = geocode_location(location)
    
    conn.execute(
        """
        INSERT INTO parties (user_id, host_name, party_name, location, latitude, longitude, date, time, description, flyer_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user['id'], host_name, party_name, location, latitude, longitude, date, time, description, flyer_path),
    )
    conn.commit()
    conn.close()  # Inserts new party into the parties database on wtm.db

    return redirect(url_for('list_page'))


# Allows the user to edit party details if necessary
@app.route('/party/<int:party_id>/edit', methods=['GET', 'POST'])
def edit_party(party_id):
    user = current_user()
    if not user:
        return redirect(url_for('login_page'))

    conn = get_db_connection()
    party = conn.execute("SELECT * FROM parties WHERE id = ?", (party_id,)).fetchone()

    # Permission check - ensure that only creator of the party can edit
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
    
    # Security Feature so that the host name still matches - S
        user_data = conn.execute("SELECT display_name FROM users WHERE id = ?", (user['id'],)).fetchone()
        
        if user_data['display_name'].lower() != host_name.lower():
            conn.close()
            return render_template('edit_party.html', party=party, user=user,
                                error=f"Host name must match your username ({user_data['display_name']}).")
        
        # Handle flyer upload - S
        flyer_path = party['flyer_path']
        if 'flyer' in request.files:
            file = request.files['flyer']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'parties', filename)
                file.save(filepath)
                flyer_path = f'uploads/parties/{filename}'
        
        # Geocode location
        latitude, longitude = geocode_location(location)

        conn.execute(
            """
            UPDATE parties
            SET host_name = ?, party_name = ?, location = ?, latitude = ?, longitude = ?, 
                date = ?, time = ?, description = ?, flyer_path = ?
            WHERE id = ?
            """,
            (host_name, party_name, location, latitude, longitude, date, time, description, flyer_path, party_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('party_detail', party_id=party_id))  # Updates parties database with new party details

    conn.close()
    return render_template('edit_party.html', party=party, user=user)


# Allows user to delete the party
@app.route('/party/<int:party_id>/delete', methods=['POST'])
def delete_party(party_id):
    user = current_user()
    if not user:
        return redirect(url_for('login_page'))

    conn = get_db_connection()
    party = conn.execute("SELECT * FROM parties WHERE id = ?", (party_id,)).fetchone()

    # Permission check: ensure only user who created can delete
    if party and party['user_id'] == user['id']:
        conn.execute("DELETE FROM parties WHERE id = ?", (party_id,))  # Deletes party from the parties database
        conn.commit()

    conn.close()
    return redirect(url_for('list_page'))


# Creates a wishlist table in wt.db so users can save parties to their wishlist
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

init_wishlist_table()


# Creates the "posts" and "comments" tables for the live feed
def init_feed_tables():
    conn = get_db_connection()
    
    # Creates posts table in wtm.db
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    
    # Creates comments table in wtm.db
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    
    conn.commit()
    conn.close()

init_feed_tables()


# Allows users table to be updated
def update_users_table():
    """Add display_name column to users table if it doesn't exist"""
    conn = get_db_connection()
    try:
        # Try to add the column
        conn.execute("ALTER TABLE users ADD COLUMN display_name TEXT")
        conn.commit()
        print("Added display_name column to users table")
    except sqlite3.OperationalError:
        # If column already exists
        pass
    conn.close()

update_users_table()


# Creates a live feed where users can post and comment on the social scene
@app.route('/feed')
def feed():
    user = current_user()
    conn = get_db_connection()
    
    # Get all posts with user info and comment count
    posts = conn.execute(
        """
        SELECT p.id,
               p.content,
               p.created_at,
               u.display_name AS username,
               COUNT(DISTINCT c.id) as comment_count
        FROM posts p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN comments c ON p.id = c.post_id
        GROUP BY p.id
        ORDER BY p.created_at DESC
        """
    ).fetchall()
    
    conn.close()
    return render_template('feed.html', posts=posts, user=user)


# Allows user to create a post in the feed
@app.route('/feed/post', methods=['POST'])
def create_post():
    user = current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401  # User must be signed in
    
    content = request.form.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Post content cannot be empty'}), 400  # There must be content in the post

    # Handle photo upload for posts -S
    photo_path = None
    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'posts', filename)
            file.save(filepath)
            photo_path = f'uploads/posts/{filename}'
    
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO posts (user_id, content, photo_path) VALUES (?, ?, ?)",
        (user['id'], content, photo_path)
    )
    conn.commit()
    conn.close()   # Adds the post to the posts table
    
    return redirect(url_for('feed'))


# Allows user to see a single post and its comments
@app.route('/feed/post/<int:post_id>')
def view_post(post_id):
    user = current_user()
    conn = get_db_connection()
    
    # From posts, select the particular post
    post = conn.execute(
        """
        SELECT p.id,
               p.user_id,
               p.content,
               p.photo_path,
               p.created_at,
               u.display_name AS username
        FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.id = ?
        """,
        (post_id,)
    ).fetchone()
    
    if not post:
        conn.close()
        return redirect(url_for('feed'))
    
    # From comments, get all comments from this post
    comments = conn.execute(
        """
        SELECT c.id,
               c.content,
               c.created_at,
               c.user_id,
               u.display_name AS username
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.post_id = ?
        ORDER BY c.created_at ASC
        """,
        (post_id,)
    ).fetchall()
    
    conn.close()
    return render_template('post_detail.html', post=post, comments=comments, user=user)


# Allows user to create a comment on a post
@app.route('/feed/post/<int:post_id>/comment', methods=['POST'])
def create_comment(post_id):
    user = current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401  # User must be logged in
    
    content = request.form.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Comment content cannot be empty'}), 400  # Comment must have content
    
    conn = get_db_connection()
    
    # Ensure that the post being commented on exists
    post = conn.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        conn.close()
        return jsonify({'error': 'Post not found'}), 404  # If the post does not exist
    
    conn.execute(
        "INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
        (post_id, user['id'], content)
    )
    conn.commit()
    conn.close()  # Adds comment to the comments table
    
    return redirect(url_for('view_post', post_id=post_id))


# Allows the creater to delete a post
@app.route('/feed/post/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    user = current_user()
    if not user:
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    
    # Ensure only the creator can delete the post
    if post and post['user_id'] == user['id']:
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
    
    conn.close()
    return redirect(url_for('feed'))


# Allows the creater to delete a comment
@app.route('/feed/comment/<int:comment_id>/delete', methods=['POST'])
def delete_comment(comment_id):
    user = current_user()
    if not user:
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    comment = conn.execute("SELECT * FROM comments WHERE id = ?", (comment_id,)).fetchone()
    
    # Ensures only the creator can delete their own comments
    if comment and comment['user_id'] == user['id']:
        post_id = comment['post_id']
        conn.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('view_post', post_id=post_id))
    
    conn.close()
    return redirect(url_for('feed'))


# Allows user to change their username
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    user = current_user()
    if not user:
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    user_data = conn.execute("SELECT display_name FROM users WHERE id = ?", (user['id'],)).fetchone()
    
    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        
        if not new_username:
            conn.close()
            return render_template('settings.html', user=user, current_username=user_data['display_name'], 
                                 error="Username cannot be empty.")  # User must have a valid username
        
        if len(new_username) < 3 or len(new_username) > 20:
            conn.close()
            return render_template('settings.html', user=user, current_username=user_data['display_name'],
                                 error="Username must be between 3 and 20 characters.")  # Username must satisfy these conditions
        
        if not new_username.replace('_', '').isalnum():
            conn.close()
            return render_template('settings.html', user=user, current_username=user_data['display_name'],
                                 error="Username can only contain letters, numbers, and underscores.")  # Username must satisfy these
        
        # Ensure username isn't already taken
        existing = conn.execute(
            "SELECT id FROM users WHERE display_name = ? AND id != ?", 
            (new_username, user['id'])
        ).fetchone()
        
        if existing:
            conn.close()
            return render_template('settings.html', user=user, current_username=user_data['display_name'],
                                 error="That username is already taken.")
        
        # Allow user to udpate their username and in wtm.db
        conn.execute("UPDATE users SET display_name = ? WHERE id = ?", (new_username, user['id']))
        conn.commit()
        session['username'] = new_username
        conn.close()
        
        return render_template('settings.html', user=user, current_username=new_username, 
                             success="Username updated successfully!")
    
    conn.close()
    return render_template('settings.html', user=user, current_username=user_data['display_name'])


# This gets user's wishlist party IDs
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


# This allows wishlist data to appear in the list route as well
@app.route('/list')
def list_page():
    user = current_user()
    conn = get_db_connection()
    parties = conn.execute(
        """
        SELECT p.id,
               p.party_name,
               p.location,
               p.latitude,
               p.longitude,
               p.date,
               p.time,
               p.description,
               p.host_name,
               p.flyer_path,
               p.created_at,
               u.username AS created_by,
               u.display_name AS verified_host
        FROM parties p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.date, p.time
        """
    ).fetchall()
    conn.close()
    
    # Gets user's wishlist
    user_wishlist = get_user_wishlist_ids(user['id']) if user else set()
    
    return render_template('list.html', parties=parties, user=user, user_wishlist=user_wishlist)

# API endpoint to get party locations for map - S
@app.route('/api/parties/map')
def parties_map_data():
    conn = get_db_connection()
    parties = conn.execute(
        """
        SELECT p.id,
               p.party_name,
               p.location,
               p.latitude,
               p.longitude,
               p.date,
               p.time,
               u.display_name AS verified_host
        FROM parties p
        JOIN users u ON p.user_id = u.id
        WHERE datetime(p.date || ' ' || p.time) >= datetime('now', 'localtime')
        AND p.latitude IS NOT NULL
        AND p.longitude IS NOT NULL
        ORDER BY datetime(p.date || ' ' || p.time)
        """
    ).fetchall()
    conn.close()
    
    # Convert to JSON format - S
    parties_data = []
    for party in parties:
        parties_data.append({
            'id': party['id'],
            'name': party['party_name'],
            'location': party['location'],
            'latitude': party['latitude'],
            'longitude': party['longitude'],
            'date': party['date'],
            'time': party['time'],
            'host': party['verified_host']
        })
    
    return jsonify(parties_data)

# This creates a wishlist page on the website
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
               p.flyer_path,
               p.created_at,
               u.username AS created_by,
               u.display_name AS verified_host,
               w.added_at
        FROM wishlist w
        JOIN parties p ON w.party_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE w.user_id = ?
        ORDER BY w.added_at DESC
        """,
        (user['id'],)
    ).fetchall()
    conn.close()  # This allows user to see all parties in their wishlist and their details
    
    # If there are no parties in a user's wishlist...
    message = "You haven't added any parties to your wishlist yet." if not parties else None
    
    return render_template('wishlist.html', parties=parties, message=message, user=user)


# Allow the user to edit their wishlist
@app.route('/party/<int:party_id>/wishlist', methods=['POST'])
def toggle_wishlist(party_id):
    user = current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    
    # Ensure that their party exists
    party = conn.execute("SELECT id FROM parties WHERE id = ?", (party_id,)).fetchone()
    if not party:
        conn.close()
        return jsonify({'error': 'Party not found'}), 404
    
    # Checks if the party is already in the wishlist
    existing = conn.execute(
        "SELECT id FROM wishlist WHERE user_id = ? AND party_id = ?",
        (user['id'], party_id)
    ).fetchone()
    
    if existing:
        # If the user would like to remove party from their wishlist
        conn.execute(
            "DELETE FROM wishlist WHERE user_id = ? AND party_id = ?",
            (user['id'], party_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'action': 'removed', 'party_id': party_id})
    else:
        # If the user would like to add a party to their wishlist
        conn.execute(
            "INSERT INTO wishlist (user_id, party_id) VALUES (?, ?)",
            (user['id'], party_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'action': 'added', 'party_id': party_id})
    

if __name__ == '__main__':
    app.run(debug=True)