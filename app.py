"""Team Calendar — Flask Backend"""
import sqlite3, json, os, datetime
from functools import wraps
from flask import Flask, request, jsonify, render_template, g
import jwt, bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'calendar.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
    return db

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None: db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            color TEXT DEFAULT '#3ECF8E',
            is_admin INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            start TEXT NOT NULL,
            end TEXT NOT NULL,
            color TEXT DEFAULT '#3ECF8E',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        # Default admin
        admin = db.execute("SELECT id FROM users WHERE username='admin'").fetchone()
        if not admin:
            pw = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
            db.execute("INSERT INTO users (username,password_hash,full_name,color,is_admin) VALUES (?,?,?,?,?)",
                       ('admin', pw, 'Administrator', '#EF4444', 1))
        db.commit()

# ===== AUTH HELPERS =====
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'error': 'Token diperlukan'}), 401
        try:
            data = jwt.decode(auth[7:], app.config['SECRET_KEY'], algorithms=['HS256'])
            g.current_user = get_db().execute("SELECT * FROM users WHERE id=?", (data['user_id'],)).fetchone()
            if not g.current_user: return jsonify({'error': 'User tidak wujud'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token tamat tempoh'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token tidak sah'}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if not g.current_user['is_admin']:
            return jsonify({'error': 'Akses admin sahaja'}), 403
        return f(*args, **kwargs)
    return decorated

# ===== AUTH ROUTES =====
@app.route('/api/register', methods=['POST'])
def register():
    db = get_db()
    data = request.get_json()
    if not data.get('username') or not data.get('password') or not data.get('full_name'):
        return jsonify({'error': 'Username, password, dan nama penuh diperlukan'}), 400
    if db.execute("SELECT id FROM users WHERE username=?", (data['username'],)).fetchone():
        return jsonify({'error': 'Username telah wujud'}), 409
    pw = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()
    db.execute("INSERT INTO users (username,password_hash,full_name,color) VALUES (?,?,?,?)",
               (data['username'], pw, data['full_name'], data.get('color', '#3ECF8E')))
    db.commit()
    return jsonify({'message': 'Pendaftaran berjaya'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    db = get_db()
    data = request.get_json()
    user = db.execute("SELECT * FROM users WHERE username=?", (data.get('username', ''),)).fetchone()
    if not user or not bcrypt.checkpw(data.get('password', '').encode(), user['password_hash'].encode()):
        return jsonify({'error': 'Username atau password salah'}), 401
    token = jwt.encode({'user_id': user['id'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)},
                        app.config['SECRET_KEY'], algorithm='HS256')
    return jsonify({'token': token, 'user': {'id': user['id'], 'username': user['username'],
        'full_name': user['full_name'], 'color': user['color'], 'is_admin': bool(user['is_admin'])}})

@app.route('/api/me', methods=['GET'])
@token_required
def me():
    u = g.current_user
    return jsonify({'id': u['id'], 'username': u['username'], 'full_name': u['full_name'],
                    'color': u['color'], 'is_admin': bool(u['is_admin'])})

# ===== EVENT ROUTES =====
@app.route('/api/events', methods=['GET'])
@token_required
def get_events():
    db = get_db()
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    query = "SELECT e.*, u.full_name AS user_name, u.color AS user_color FROM events e JOIN users u ON e.user_id=u.id"
    params = []
    if start and end:
        query += " WHERE e.end >= ? AND e.start <= ?"
        params = [start, end]
    events = db.execute(query + " ORDER BY e.start", params).fetchall()
    return jsonify([{'id': e['id'], 'title': e['title'], 'start': e['start'], 'end': e['end'],
        'description': e['description'], 'color': e['color'], 'userId': e['user_id'],
        'userName': e['user_name'], 'userColor': e['user_color'],
        'editable': e['user_id'] == g.current_user['id']} for e in events])

@app.route('/api/events', methods=['POST'])
@token_required
def create_event():
    db = get_db()
    data = request.get_json()
    db.execute("INSERT INTO events (user_id,title,description,start,end,color) VALUES (?,?,?,?,?,?)",
               (g.current_user['id'], data['title'], data.get('description', ''),
                data['start'], data.get('end', data['start']), data.get('color', g.current_user['color'])))
    db.commit()
    return jsonify({'message': 'Event dicipta', 'id': db.execute("SELECT last_insert_rowid()").fetchone()[0]}), 201

@app.route('/api/events/<int:event_id>', methods=['PUT'])
@token_required
def update_event(event_id):
    db = get_db()
    event = db.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    if not event: return jsonify({'error': 'Event tidak dijumpai'}), 404
    if event['user_id'] != g.current_user['id'] and not g.current_user['is_admin']:
        return jsonify({'error': 'Hanya owner atau admin boleh edit'}), 403
    data = request.get_json()
    db.execute("UPDATE events SET title=?, description=?, start=?, end=?, color=? WHERE id=?",
               (data.get('title', event['title']), data.get('description', event['description']),
                data.get('start', event['start']), data.get('end', event['end']),
                data.get('color', event['color']), event_id))
    db.commit()
    return jsonify({'message': 'Event dikemaskini'})

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
@token_required
def delete_event(event_id):
    db = get_db()
    event = db.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    if not event: return jsonify({'error': 'Event tidak dijumpai'}), 404
    if event['user_id'] != g.current_user['id'] and not g.current_user['is_admin']:
        return jsonify({'error': 'Hanya owner atau admin boleh delete'}), 403
    db.execute("DELETE FROM events WHERE id=?", (event_id,))
    db.commit()
    return jsonify({'message': 'Event dipadam'})

# ===== ADMIN ROUTES =====
@app.route('/api/users', methods=['GET'])
@admin_required
def get_users():
    users = get_db().execute("SELECT id,username,full_name,color,is_admin,created_at FROM users ORDER BY id").fetchall()
    return jsonify([{'id': u['id'], 'username': u['username'], 'full_name': u['full_name'],
        'color': u['color'], 'is_admin': bool(u['is_admin']), 'created_at': u['created_at']} for u in users])

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    db = get_db()
    data = request.get_json()
    if data.get('password'):
        pw = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()
        db.execute("UPDATE users SET password_hash=? WHERE id=?", (pw, user_id))
    db.execute("UPDATE users SET full_name=?, color=?, is_admin=? WHERE id=?",
               (data.get('full_name'), data.get('color'), int(data.get('is_admin', False)), user_id))
    db.commit()
    return jsonify({'message': 'User dikemaskini'})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    if user_id == g.current_user['id']:
        return jsonify({'error': 'Tidak boleh delete diri sendiri'}), 400
    db = get_db()
    db.execute("DELETE FROM events WHERE user_id=?", (user_id,))
    db.execute("DELETE FROM users WHERE id=?", (user_id,))
    db.commit()
    return jsonify({'message': 'User dipadam'})

# ===== STATIC PAGES =====
@app.route('/')
def index():
    return render_template('calendar.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
