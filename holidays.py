"""
Malaysia Calendar API fetcher — Public Holidays + School Holidays (Zon B).
Sources: https://mycal-api.huijun00100101.workers.dev/v1 (Junhui20/malaysia-calendar-api)
"""
import sqlite3, os, json, urllib.request
from datetime import date, timedelta

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'calendar.db')
API_BASE = "https://mycal-api.huijun00100101.workers.dev/v1"

# Default state for Zon B (Selangor as representative)
STATE = "selangor"

def fetch_json(url):
    """Fetch JSON from API with error handling"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'FamilyCalendar/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"⚠️  API fetch failed: {url} — {e}")
        return None

def date_range(start_str, end_str):
    """Generate all dates between start and end inclusive"""
    start = date.fromisoformat(start_str)
    end = date.fromisoformat(end_str)
    current = start
    while current <= end:
        yield current.isoformat()
        current += timedelta(days=1)

def run():
    if not os.path.exists(DB):
        print("❌ DB not found — run app.py first")
        return

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Get or create system user
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

    # Clear old holidays
    cur.execute("DELETE FROM events WHERE user_id=? AND category='cuti'", (sys_uid,))
    conn.commit()

    inserted = 0
    icons = {
        'awal-muharam': '🌙', 'deepavali': '🪔', 'krismas': '🎄', 'tahun-baharu': '🎉',
        'thaipusam': '🕉️', 'tahun-baharu-cina': '🧧', 'hari-nuzul': '🕌',
        'hari-raya-aidilfitri': '🕌', 'hari-pekerja': '👷', 'hari-raya-qurban': '🕋',
        'hari-wesak': '🕉️', 'agong': '👑', 'maulidur-rasul': '🕌',
        'hari-kebangsaan': '🇲🇾', 'hari-malaysia': '🇲🇾',
        'sultan': '👑',
    }

    def get_icon(holiday_id, name):
        for key, icon in icons.items():
            if key in holiday_id.lower() or key in name.lower():
                return icon
        return '📅'

    # ===== FETCH PUBLIC HOLIDAYS =====
    print("Fetching public holidays from API...")
    data = fetch_json(f"{API_BASE}/holidays?year=2026&state={STATE}")
    if data and 'data' in data:
        for h in data['data']:
            dt = h['date']
            nm = h['name']['ms']
            icon = get_icon(h.get('id',''), nm)
            cur.execute(
                "INSERT INTO events (user_id,title,description,start,\"end\",color,category) VALUES (?,?,?,?,?,?,?)",
                (sys_uid, f"{icon} {nm}", 'Cuti Umum Malaysia 🇲🇾', dt, dt, '#6B7280', 'cuti')
            )
            inserted += 1
        print(f"  ✅ {len(data['data'])} cuti umum")

    # ===== FETCH SCHOOL HOLIDAYS ZON B =====
    print("Fetching school holidays Zon B from API...")
    data = fetch_json(f"{API_BASE}/school/holidays?year=2026&state={STATE}")
    if data and 'data' in data:
        school_count = 0
        for h in data['data']:
            nm = h['name']['ms']
            start = h['startDate']
            end = h['endDate']
            for d in date_range(start, end):
                cur.execute(
                    "INSERT INTO events (user_id,title,description,start,\"end\",color,category) VALUES (?,?,?,?,?,?,?)",
                    (sys_uid, f"📚 {nm}",
                     f"Cuti Sekolah Zon B — {h['days']} hari",
                     d, d, '#94A3B8', 'cuti')
                )
                inserted += 1
                school_count += 1
        print(f"  ✅ {len(data['data'])} tempoh cuti sekolah ({school_count} hari)")

    conn.commit()
    conn.close()
    print(f"\n🎉 Total: {inserted} events cuti untuk 2026")

if __name__ == '__main__':
    run()
