# Team Calendar — Shared Planning Dashboard

Full-stack **team calendar app** dengan user login, event management, dan admin panel. Setiap user hanya boleh edit planning sendiri, tapi semua orang boleh lihat aktiviti team untuk bulan semasa.

Dibina dengan **Flask + SQLite + FullCalendar + Supabase Green Theme**.

## ✨ Features

| Feature | Details |
|---------|---------|
| 🔐 **User Auth** | Register, login, JWT token — setiap user akaun sendiri |
| 📅 **FullCalendar** | Month & week view, drag-drop, resize events |
| 👤 **User Events** | Setiap user edit event sendiri sahaja — tak boleh kacau orang lain |
| 👥 **Team View** | Semua event team dipaparkan dalam satu calendar — setiap orang warna berbeza |
| ⚙️ **Admin Panel** | Tambah/edit/delete users, tukar warna, promote admin |
| 🎨 **Legend Bar** | Senarai ahli team beserta warna masing-masing |
| 📝 **Event Modal** | Tambah/edit/padam acara dengan tajuk, deskripsi, mula/tamat |
| 🗄️ **SQLite DB** | Users + events tables, foreign key validation |
| 🟢 **Supabase Green** | Professional green theme, Inter font, clean UI |
| 📱 **Responsive** | Mobile-friendly — guna dari phone pun OK |

## 🚀 Quick Start

```bash
cd team-calendar
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
# Buka http://localhost:5000
```

### Default Admin Login

- **Username:** `admin`
- **Password:** `admin123`

## 📁 Structure

```
team-calendar/
├── app.py              ← Flask backend (auth, events API, user mgmt)
├── requirements.txt    ← Python dependencies
├── templates/
│   ├── login.html      ← Login page
│   ├── register.html   ← Registration page
│   ├── calendar.html   ← Main dashboard (FullCalendar)
│   └── admin.html      ← Admin panel (user management)
└── calendar.db          ← SQLite database (auto-created)
```

## 🔌 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/register` | No | Daftar user baru |
| POST | `/api/login` | No | Login — return JWT |
| GET | `/api/me` | User | Get current user info |
| GET | `/api/events` | User | Get events (filter by date range) |
| POST | `/api/events` | User | Create event |
| PUT | `/api/events/:id` | Owner/Admin | Update event |
| DELETE | `/api/events/:id` | Owner/Admin | Delete event |
| GET | `/api/users` | Admin | List all users |
| PUT | `/api/users/:id` | Admin | Update user |
| DELETE | `/api/users/:id` | Admin | Delete user |

## 🎨 Theme Credits

Design inspired by **[Supabase shadcn/ui theme](https://21st.dev/serafimcloud/supabase)** on 21st.dev — green professional, clean, modern.

## 🛠️ Tech Stack

- **Backend:** Flask + SQLite + PyJWT + bcrypt
- **Frontend:** FullCalendar v6 + Vanilla JavaScript
- **Font:** Inter (Google Fonts)
- **Deploy:** Anywhere — single `python app.py`

## 📝 License

MIT
