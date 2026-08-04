"""
Malaysia Calendar API — Zone-aware public holidays + school holidays.
Sources: https://mycal-api.huijun00100101.workers.dev/v1
Zon A: Perlis, Kedah, Kelantan, Terengganu, Johor (Sunday first day)
Zon B: Selangor, KL, Putrajaya, NS, Melaka, Pahang, Perak, Penang, Sabah, Sarawak, Labuan (Monday first day)
"""
import sqlite3, os, json, urllib.request
from datetime import date, timedelta

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'calendar.db')
API_BASE = "https://mycal-api.huijun00100101.workers.dev/v1"

# Zone → state mapping for API queries
ZONE_STATE = {
    'A': 'johor',      # Representative state for Zon A
    'B': 'selangor',   # Representative state for Zon B
}

# Color schemes for zones
ZONE_BG = {
    'A': {'primary': '#0F172A', 'accent': '#D97706', 'gradient': 'linear-gradient(135deg,#1A1423,#3D1A0A,#1E3A5F,#0F172A)'},
    'B': {'primary': '#1A1423', 'accent': '#8B5CF6', 'gradient': 'linear-gradient(135deg,#1A1423,#2D1B3E,#1E3A5F,#0F172A)'},
}

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'FamilyCalendar/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"⚠️  API fetch failed: {e}")
        return None

def date_range(start_str, end_str):
    start = date.fromisoformat(start_str)
    end = date.fromisoformat(end_str)
    current = start
    while current <= end:
        yield current.isoformat()
        current += timedelta(days=1)

def run(zone=None):
    if not os.path.exists(DB):
        print("❌ DB not found — run app.py first")
        return

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Auto-detect zone from settings if not specified
    if zone is None:
        row = cur.execute("SELECT value FROM settings WHERE key='zone'").fetchone()
        zone = row['value'] if row else 'B'
    if zone not in ZONE_STATE:
        print(f"⚠️  Unknown zone '{zone}', defaulting to B")
        zone = 'B'

    state = ZONE_STATE[zone]
    print(f"📍 Zone {zone} → State: {state}")

    # System user
    row = cur.execute("SELECT id FROM users WHERE username='_SYSTEM'").fetchone()
    if row:
        sys_uid = row[0]
    else:
        import bcrypt
        pw = bcrypt.hashpw('__system__'.encode(), bcrypt.gensalt()).decode()
        cur.execute("INSERT INTO users (username,password_hash,full_name,color,is_admin) VALUES (?,?,?,?,?)",
                   ('_SYSTEM', pw, '📅 Sistem Cuti', '#9CA3AF', 0))
        conn.commit()
        sys_uid = cur.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Clear old
    cur.execute("DELETE FROM events WHERE user_id=? AND category='cuti'", (sys_uid,))
    conn.commit()

    inserted = 0
    icons = {
        'awal-muharam':'🌙','deepavali':'🪔','krismas':'🎄','tahun-baharu':'🎉',
        'thaipusam':'🕉️','tahun-baharu-cina':'🧧','hari-nuzul':'🕌',
        'hari-raya-aidilfitri':'🕌','hari-pekerja':'👷','hari-raya-qurban':'🕋',
        'hari-wesak':'🕉️','agong':'👑','maulidur-rasul':'🕌',
        'hari-kebangsaan':'🇲🇾','hari-malaysia':'🇲🇾','sultan':'👑',
    }

    def get_icon(hid, nm):
        for k, icon in icons.items():
            if k in hid.lower() or k in nm.lower(): return icon
        return '📅'

    # === Public Holidays ===
    print("📡 Fetching public holidays...")
    data = fetch_json(f"{API_BASE}/holidays?year=2026&state={state}")
    if data and 'data' in data:
        for h in data['data']:
            dt = h['date']; nm = h['name']['ms']; icon = get_icon(h.get('id',''), nm)
            cur.execute("INSERT INTO events (user_id,title,description,start,\"end\",color,category) VALUES (?,?,?,?,?,?,?)",
                       (sys_uid, f"{icon} {nm}", 'Cuti Umum Malaysia 🇲🇾', dt, dt, '#6B7280', 'cuti'))
            inserted += 1
        print(f"  ✅ {len(data['data'])} cuti umum")

    # === School Holidays ===
    print("📡 Fetching school holidays...")
    data = fetch_json(f"{API_BASE}/school/holidays?year=2026&group={zone}")
    if data and 'data' in data:
        school_count = 0
        for h in data['data']:
            nm = h['name']['ms']; start = h['startDate']; end = h['endDate']
            for d in date_range(start, end):
                cur.execute("INSERT INTO events (user_id,title,description,start,\"end\",color,category) VALUES (?,?,?,?,?,?,?)",
                           (sys_uid, f"📚 {nm}", f"Cuti Sekolah Zon {zone} — {h['days']} hari", d, d, '#94A3B8', 'cuti'))
                inserted += 1; school_count += 1
        print(f"  ✅ {len(data['data'])} tempoh cuti sekolah ({school_count} hari)")

    conn.commit()
    conn.close()
    print(f"\n🎉 Total: {inserted} events cuti Zon {zone} untuk 2026")
    return zone

if __name__ == '__main__':
    run()
