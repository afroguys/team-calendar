"""
Malaysian Public Holidays + School Holidays (Zon B) data for 2026.
Auto-fetcher & generator. Run this to populate the calendar database.
"""
import sqlite3, os
from datetime import date

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'calendar.db')

# ===== 2026 MALAYSIAN PUBLIC HOLIDAYS =====
PUBLIC_HOLIDAYS_2026 = [
    ("Tahun Baru 2026", "2026-01-01", "🎉"),
    ("Hari Wilayah Persekutuan", "2026-02-01", "🏙️"),
    ("Tahun Baru Cina", "2026-02-17", "🧧"),
    ("Tahun Baru Cina (Hari Kedua)", "2026-02-18", "🧧"),
    ("Hari Pekerja", "2026-05-01", "👷"),
    ("Hari Wesak", "2026-05-24", "🕉️"),
    ("Hari Keputeraan Agong", "2026-06-01", "👑"),
    ("Israk Mikraj", "2026-06-05", "🕌"),
    ("Awal Ramadan", "2026-06-07", "🌙"),
    ("Hari Raya Aidilfitri", "2026-07-06", "🕌"),
    ("Hari Raya Aidilfitri (Hari Kedua)", "2026-07-07", "🕌"),
    ("Hari Merdeka", "2026-08-31", "🇲🇾"),
    ("Hari Raya Haji", "2026-09-12", "🕋"),
    ("Hari Malaysia", "2026-09-16", "🇲🇾"),
    ("Awal Muharram", "2026-10-02", "🌙"),
    ("Deepavali", "2026-10-30", "🪔"),
    ("Maulidur Rasul", "2026-12-11", "🕌"),
    ("Hari Krismas", "2026-12-25", "🎄"),
]

# ===== 2026 CUTI SEKOLAH ZON B =====
SCHOOL_HOLIDAYS_ZONB_2026 = [
    ("Cuti Sekolah Penggal 1", "2026-02-28", "📚"),
    ("Cuti Sekolah Penggal 1", "2026-03-01", "📚"),
    ("Cuti Sekolah Penggal 1", "2026-03-02", "📚"),
    ("Cuti Sekolah Penggal 1", "2026-03-03", "📚"),
    ("Cuti Sekolah Penggal 1", "2026-03-04", "📚"),
    ("Cuti Sekolah Penggal 1", "2026-03-05", "📚"),
    ("Cuti Sekolah Penggal 1", "2026-03-06", "📚"),
    ("Cuti Sekolah Penggal 1", "2026-03-07", "📚"),
    ("Cuti Sekolah Penggal 1", "2026-03-08", "📚"),
    ("Cuti Sekolah Penggal 2", "2026-05-22", "📚"),
    ("Cuti Sekolah Penggal 2", "2026-05-23", "📚"),
    ("Cuti Sekolah Penggal 2", "2026-05-24", "📚"),
    ("Cuti Sekolah Penggal 2", "2026-05-25", "📚"),
    ("Cuti Sekolah Penggal 2", "2026-05-26", "📚"),
    ("Cuti Sekolah Penggal 2", "2026-05-27", "📚"),
    ("Cuti Sekolah Penggal 2", "2026-05-28", "📚"),
    ("Cuti Sekolah Penggal 2", "2026-05-29", "📚"),
    ("Cuti Sekolah Penggal 2", "2026-05-30", "📚"),
    ("Cuti Sekolah Penggal 2", "2026-05-31", "📚"),
    ("Cuti Sekolah Penggal 3", "2026-09-12", "📚"),
    ("Cuti Sekolah Penggal 3", "2026-09-13", "📚"),
    ("Cuti Sekolah Penggal 3", "2026-09-14", "📚"),
    ("Cuti Sekolah Penggal 3", "2026-09-15", "📚"),
    ("Cuti Sekolah Penggal 3", "2026-09-16", "📚"),
    ("Cuti Sekolah Penggal 3", "2026-09-17", "📚"),
    ("Cuti Sekolah Penggal 3", "2026-09-18", "📚"),
    ("Cuti Sekolah Penggal 3", "2026-09-19", "📚"),
    ("Cuti Sekolah Penggal 3", "2026-09-20", "📚"),
    ("Cuti Akhir Tahun", "2026-12-12", "📚"),
    ("Cuti Akhir Tahun", "2026-12-13", "📚"),
    ("Cuti Akhir Tahun", "2026-12-14", "📚"),
    ("Cuti Akhir Tahun", "2026-12-15", "📚"),
    ("Cuti Akhir Tahun", "2026-12-16", "📚"),
    ("Cuti Akhir Tahun", "2026-12-17", "📚"),
    ("Cuti Akhir Tahun", "2026-12-18", "📚"),
    ("Cuti Akhir Tahun", "2026-12-19", "📚"),
    ("Cuti Akhir Tahun", "2026-12-20", "📚"),
    ("Cuti Akhir Tahun", "2026-12-21", "📚"),
    ("Cuti Akhir Tahun", "2026-12-22", "📚"),
    ("Cuti Akhir Tahun", "2026-12-23", "📚"),
    ("Cuti Akhir Tahun", "2026-12-24", "📚"),
    ("Cuti Akhir Tahun", "2026-12-25", "📚"),
    ("Cuti Akhir Tahun", "2026-12-26", "📚"),
    ("Cuti Akhir Tahun", "2026-12-27", "📚"),
    ("Cuti Akhir Tahun", "2026-12-28", "📚"),
    ("Cuti Akhir Tahun", "2026-12-29", "📚"),
    ("Cuti Akhir Tahun", "2026-12-30", "📚"),
    ("Cuti Akhir Tahun", "2026-12-31", "📚"),
    ("Cuti Akhir Tahun", "2027-01-01", "📚"),
    ("Cuti Akhir Tahun", "2027-01-02", "📚"),
    ("Cuti Akhir Tahun", "2027-01-03", "📚"),
]

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

    # Insert all holidays (public + school)
    all_holidays = [(t, d, i) for t, d, i in PUBLIC_HOLIDAYS_2026]
    all_holidays += [(t, d, i) for t, d, i in SCHOOL_HOLIDAYS_ZONB_2026]

    inserted = 0
    for title, d, icon in all_holidays:
        cur.execute(
            "INSERT INTO events (user_id,title,description,start,\"end\",color,category) VALUES (?,?,?,?,?,?,?)",
            (sys_uid, f"{icon} {title}",
             'Auto-generated — Cuti Umum & Sekolah Malaysia (Zon B)',
             d, d, '#6B7280', 'cuti')
        )
        inserted += 1

    conn.commit()
    conn.close()
    print(f"✅ {inserted} cuti dimasukkan ({len(PUBLIC_HOLIDAYS_2026)} umum + {len(SCHOOL_HOLIDAYS_ZONB_2026)} sekolah Zon B)")

if __name__ == '__main__':
    run()
