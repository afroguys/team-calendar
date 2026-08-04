"""Family Calendar — Flask Backend"""
import sqlite3, json, os, datetime
from functools import wraps
from flask import Flask, request, jsonify, render_template, g
import jwt, bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'calendar.db')

CATEGORIES = {
    'merah': {'id':'merah','label':'Kecemasan / Doktor','color':'#EF4444','icon':'🚨'},
    'hijau': {'id':'hijau','label':'Cuti & Percutian','color':'#22C55E','icon':'✈️'},
    'kuning': {'id':'kuning','label':'Hari Lahir / Ulang Tahun','color':'#EAB308','icon':'🎂'},
    'biru': {'id':'biru','label':'Tugasan Harian','color':'#3B82F6','icon':'📋'},
    'ungu': {'id':'ungu','label':'Sekolah / Aktiviti','color':'#8B5CF6','icon':'📚'},
    'oren': {'id':'oren','label':'Sukan / Riadah','color':'#F97316','icon':'⚽'},
    'cuti': {'id':'cuti','label':'Cuti Umum / Sekolah','color':'#6B7280','icon':'🇲🇾'},
}

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA foreign_keys=ON")
    return db

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None: db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, full_name TEXT NOT NULL, color TEXT DEFAULT '#3B82F6',
            is_admin INTEGER DEFAULT 0, created_at TEXT DEFAULT (datetime('now','localtime'))
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            title TEXT NOT NULL, description TEXT DEFAULT '',
            start TEXT NOT NULL, "end" TEXT NOT NULL, color TEXT DEFAULT '#3B82F6',
            category TEXT DEFAULT 'biru', created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS birthdays (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, date TEXT NOT NULL,
            user_id INTEGER, note TEXT DEFAULT '',
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS chores (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
            assigned_to INTEGER, done INTEGER DEFAULT 0, due_date TEXT,
            created_by INTEGER NOT NULL,
            FOREIGN KEY(assigned_to) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE CASCADE
        )''')
        # Default settings
        if not db.execute("SELECT key FROM settings WHERE key='family_name'").fetchone():
            db.execute("INSERT OR IGNORE INTO settings VALUES ('family_name','Keluarga Saya')")
            db.execute("INSERT OR IGNORE INTO settings VALUES ('allow_register','0')")
        # Default admin
        if not db.execute("SELECT id FROM users WHERE username='admin'").fetchone():
            pw = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
            db.execute("INSERT INTO users (username,password_hash,full_name,color,is_admin) VALUES (?,?,?,?,?)",
                       ('admin', pw, 'Ayah', '#EF4444', 1))
            # Sample members: Ibu, Anak
            pw2 = bcrypt.hashpw('member123'.encode(), bcrypt.gensalt()).decode()
            db.execute("INSERT INTO users (username,password_hash,full_name,color) VALUES (?,?,?,?)",
                       ('ibu', pw2, 'Ibu', '#8B5CF6'))
            db.execute("INSERT INTO users (username,password_hash,full_name,color) VALUES (?,?,?,?)",
                       ('anak', pw2, 'Anak', '#22C55E'))
            # Sample birthdays
            db.execute("INSERT INTO birthdays (name,date,note) VALUES (?,?,?)",('Ayah','1985-03-15','Surprise party!'))
            db.execute("INSERT INTO birthdays (name,date,note) VALUES (?,?,?)",('Ibu','1987-07-22','Hadiah jam'))
            db.execute("INSERT INTO birthdays (name,date,note) VALUES (?,?,?)",('Anak','2015-11-08','Kek coklat'))
            # Sample chores
            db.execute("INSERT INTO chores (title,assigned_to,done,created_by) VALUES (?,?,?,?)",('Kemas bilik',3,0,1))
            db.execute("INSERT INTO chores (title,assigned_to,done,created_by) VALUES (?,?,?,?)",('Beli barang dapur',2,0,1))
            db.execute("INSERT INTO chores (title,assigned_to,done,created_by) VALUES (?,?,?,?)",('Basuh kereta',1,0,1))
        db.commit()

        # Auto-import Malaysian holidays if not yet imported
        has_holidays = db.execute("SELECT COUNT(*) AS c FROM events WHERE category='cuti'").fetchone()['c']
        if has_holidays == 0:
            try:
                from holidays import run as import_holidays
                import_holidays()
            except Exception as e:
                print(f"Holiday import skipped: {e}")

# ===== AUTH HELPERS =====
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization','')
        if not auth.startswith('Bearer '): return jsonify({'error':'Token diperlukan'}),401
        try:
            data = jwt.decode(auth[7:], app.config['SECRET_KEY'], algorithms=['HS256'])
            g.current_user = get_db().execute("SELECT * FROM users WHERE id=?",(data['user_id'],)).fetchone()
            if not g.current_user: return jsonify({'error':'User tidak wujud'}),401
        except jwt.ExpiredSignatureError: return jsonify({'error':'Token tamat tempoh'}),401
        except jwt.InvalidTokenError: return jsonify({'error':'Token tidak sah'}),401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if not g.current_user['is_admin']: return jsonify({'error':'Admin sahaja'}),403
        return f(*args, **kwargs)
    return decorated

# ===== SETTINGS =====
@app.route('/api/settings', methods=['GET'])
def get_settings():
    rows = get_db().execute("SELECT key,value FROM settings").fetchall()
    return jsonify({r['key']:r['value'] for r in rows})

@app.route('/api/settings', methods=['PUT'])
@admin_required
def update_settings():
    data = request.get_json()
    db = get_db()
    for k,v in data.items():
        db.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)",(k,str(v)))
    db.commit()
    return jsonify({'message':'Tetapan dikemaskini'})

# ===== AUTH =====
@app.route('/api/register', methods=['POST'])
def register():
    db = get_db()
    # Check if registration is allowed
    allow = db.execute("SELECT value FROM settings WHERE key='allow_register'").fetchone()
    if not allow or allow['value'] != '1':
        return jsonify({'error':'Pendaftaran awam ditutup — hubungi admin'}),403
    data = request.get_json()
    if not data.get('username') or not data.get('password') or not data.get('full_name'):
        return jsonify({'error':'Semua field diperlukan'}),400
    if db.execute("SELECT id FROM users WHERE username=?",(data['username'],)).fetchone():
        return jsonify({'error':'Username telah wujud'}),409
    pw = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()
    db.execute("INSERT INTO users (username,password_hash,full_name,color) VALUES (?,?,?,?)",
               (data['username'],pw,data['full_name'],data.get('color','#3B82F6')))
    db.commit()
    return jsonify({'message':'Pendaftaran berjaya'}),201

@app.route('/api/login', methods=['POST'])
def login():
    db = get_db()
    data = request.get_json()
    user = db.execute("SELECT * FROM users WHERE username=?",(data.get('username',''),)).fetchone()
    if not user or not bcrypt.checkpw(data.get('password','').encode(), user['password_hash'].encode()):
        return jsonify({'error':'Username atau password salah'}),401
    token = jwt.encode({'user_id':user['id'],'exp':datetime.datetime.utcnow()+datetime.timedelta(days=7)},
                        app.config['SECRET_KEY'], algorithm='HS256')
    return jsonify({'token':token,'user':{'id':user['id'],'username':user['username'],
        'full_name':user['full_name'],'color':user['color'],'is_admin':bool(user['is_admin'])}})

@app.route('/api/me', methods=['GET'])
@token_required
def me():
    u = g.current_user
    return jsonify({'id':u['id'],'username':u['username'],'full_name':u['full_name'],
                    'color':u['color'],'is_admin':bool(u['is_admin'])})

# ===== EVENTS =====
@app.route('/api/events', methods=['GET'])
@token_required
def get_events():
    db = get_db()
    start = request.args.get('start',''); end = request.args.get('end','')
    q = "SELECT e.*, u.full_name AS user_name, u.color AS user_color FROM events e JOIN users u ON e.user_id=u.id"
    params = []
    if start and end: q += " WHERE e.\"end\" >= ? AND e.start <= ?"; params = [start,end]
    events = db.execute(q+" ORDER BY e.start", params).fetchall()
    return jsonify([{'id':e['id'],'title':e['title'],'start':e['start'],'end':e['end'],
        'description':e['description'],'color':e['color'],'category':e['category'],
        'userId':e['user_id'],'userName':e['user_name'],'userColor':e['user_color'],
        'editable':(e['user_id']==g.current_user['id'] and e['category']!='cuti')} for e in events])

@app.route('/api/events', methods=['POST'])
@token_required
def create_event():
    db = get_db()
    data = request.get_json()
    cat = data.get('category','biru')
    color = data.get('color') or CATEGORIES.get(cat,{}).get('color', g.current_user['color'])
    db.execute("INSERT INTO events (user_id,title,description,start,\"end\",color,category) VALUES (?,?,?,?,?,?,?)",
               (g.current_user['id'],data['title'],data.get('description',''),data['start'],
                data.get('end',data['start']),color,cat))
    db.commit(); eid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    return jsonify({'message':'Event dicipta','id':eid}),201

@app.route('/api/events/<int:event_id>', methods=['PUT'])
@token_required
def update_event(event_id):
    db = get_db()
    event = db.execute("SELECT * FROM events WHERE id=?",(event_id,)).fetchone()
    if not event: return jsonify({'error':'Event tidak dijumpai'}),404
    if event['user_id']!=g.current_user['id'] and not g.current_user['is_admin']:
        return jsonify({'error':'Hanya owner atau admin'}),403
    data = request.get_json()
    cat = data.get('category',event['category'])
    color = data.get('color') or CATEGORIES.get(cat,{}).get('color', event['color'])
    db.execute("UPDATE events SET title=?,description=?,start=?,\"end\"=?,color=?,category=? WHERE id=?",
               (data.get('title',event['title']),data.get('description',event['description']),
                data.get('start',event['start']),data.get('end',event['end']),color,cat,event_id))
    db.commit()
    return jsonify({'message':'Event dikemaskini'})

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
@token_required
def delete_event(event_id):
    db = get_db()
    event = db.execute("SELECT * FROM events WHERE id=?",(event_id,)).fetchone()
    if not event: return jsonify({'error':'Event tidak dijumpai'}),404
    if event['user_id']!=g.current_user['id'] and not g.current_user['is_admin']:
        return jsonify({'error':'Hanya owner atau admin'}),403
    db.execute("DELETE FROM events WHERE id=?",(event_id,)); db.commit()
    return jsonify({'message':'Event dipadam'})

# ===== BIRTHDAYS =====
@app.route('/api/birthdays', methods=['GET'])
@token_required
def get_birthdays():
    bdays = get_db().execute("SELECT * FROM birthdays ORDER BY date").fetchall()
    today = datetime.date.today()
    result = []
    for b in bdays:
        bdate = datetime.datetime.strptime(b['date'],'%Y-%m-%d').date()
        next_bday = bdate.replace(year=today.year)
        if next_bday < today: next_bday = next_bday.replace(year=today.year+1)
        days_left = (next_bday - today).days
        result.append({'id':b['id'],'name':b['name'],'date':b['date'],'note':b['note'],
                       'daysLeft':days_left,'nextDate':next_bday.isoformat(),
                       'age':today.year - bdate.year})
    result.sort(key=lambda x: x['daysLeft'])
    return jsonify(result)

@app.route('/api/birthdays', methods=['POST'])
@token_required
def create_birthday():
    db = get_db()
    data = request.get_json()
    db.execute("INSERT INTO birthdays (name,date,note,user_id) VALUES (?,?,?,?)",
               (data['name'],data['date'],data.get('note',''),data.get('user_id')))
    db.commit()
    return jsonify({'message':'Birthday disimpan'}),201

@app.route('/api/birthdays/<int:bid>', methods=['DELETE'])
@token_required
def delete_birthday(bid):
    db = get_db()
    db.execute("DELETE FROM birthdays WHERE id=?",(bid,)); db.commit()
    return jsonify({'message':'Birthday dipadam'})

# ===== CHORES =====
@app.route('/api/chores', methods=['GET'])
@token_required
def get_chores():
    chores = get_db().execute("SELECT c.*, u.full_name AS assigned_name, u.color AS assigned_color FROM chores c LEFT JOIN users u ON c.assigned_to=u.id ORDER BY c.id").fetchall()
    return jsonify([{'id':c['id'],'title':c['title'],'assignedTo':c['assigned_to'],
        'assignedName':c['assigned_name'] or '--','assignedColor':c['assigned_color'] or '#94A3B8',
        'done':bool(c['done']),'dueDate':c['due_date'],
        'editable':c['created_by']==g.current_user['id'] or g.current_user['is_admin']} for c in chores])

@app.route('/api/chores', methods=['POST'])
@token_required
def create_chore():
    db = get_db()
    data = request.get_json()
    db.execute("INSERT INTO chores (title,assigned_to,created_by,due_date) VALUES (?,?,?,?)",
               (data['title'],data.get('assigned_to'),g.current_user['id'],data.get('due_date')))
    db.commit()
    return jsonify({'message':'Tugasan ditambah'}),201

@app.route('/api/chores/<int:cid>', methods=['PUT'])
@token_required
def update_chore(cid):
    db = get_db()
    chore = db.execute("SELECT * FROM chores WHERE id=?",(cid,)).fetchone()
    if not chore: return jsonify({'error':'Tidak dijumpai'}),404
    data = request.get_json()
    if 'done' in data:
        db.execute("UPDATE chores SET done=? WHERE id=?",(int(data['done']),cid))
    if 'title' in data:
        db.execute("UPDATE chores SET title=?,assigned_to=? WHERE id=?",(data['title'],data.get('assigned_to'),cid))
    db.commit()
    return jsonify({'message':'Tugasan dikemaskini'})

@app.route('/api/chores/<int:cid>', methods=['DELETE'])
@token_required
def delete_chore(cid):
    db = get_db()
    db.execute("DELETE FROM chores WHERE id=?",(cid,)); db.commit()
    return jsonify({'message':'Tugasan dipadam'})

# ===== USERS (ANY USER can list for chore assignment) =====
@app.route('/api/users', methods=['GET'])
@token_required
def get_users():
    users = get_db().execute("SELECT id,username,full_name,color,is_admin,created_at FROM users WHERE username!='_SYSTEM' ORDER BY id").fetchall()
    return jsonify([{'id':u['id'],'username':u['username'],'full_name':u['full_name'],
        'color':u['color'],'is_admin':bool(u['is_admin']),'created_at':u['created_at']} for u in users])

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    db = get_db()
    data = request.get_json()
    if data.get('password'):
        pw = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()
        db.execute("UPDATE users SET password_hash=? WHERE id=?",(pw,user_id))
    db.execute("UPDATE users SET full_name=?,color=?,is_admin=? WHERE id=?",
               (data.get('full_name'),data.get('color'),int(data.get('is_admin',False)),user_id))
    db.commit()
    return jsonify({'message':'User dikemaskini'})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    if user_id == g.current_user['id']: return jsonify({'error':'Tidak boleh delete sendiri'}),400
    db = get_db()
    db.execute("DELETE FROM chores WHERE assigned_to=?",(user_id,))
    db.execute("DELETE FROM events WHERE user_id=?",(user_id,))
    db.execute("DELETE FROM users WHERE id=?",(user_id,))
    db.commit()
    return jsonify({'message':'User dipadam'})

# ===== STATIC PAGES =====
@app.route('/')
def index(): return render_template('calendar.html')
@app.route('/login')
def login_page(): return render_template('login.html')
@app.route('/register')
def register_page(): return render_template('register.html')
@app.route('/admin')
def admin_page(): return render_template('admin.html')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
