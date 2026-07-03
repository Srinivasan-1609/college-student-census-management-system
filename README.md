# Computer Based Census Management System
## College Mini Project | Python Flask + SQLite

---

### Project Overview
A fully web-based Census Management System that allows government/administration users to collect, store, manage, search, update and generate citizen census data digitally.

---

### Technology Stack
| Layer      | Technology          |
|------------|---------------------|
| Frontend   | HTML5, CSS3, JavaScript (Vanilla) |
| Backend    | Python 3 + Flask    |
| Database   | SQLite (via sqlite3) |
| Icons      | Font Awesome 6      |
| Charts     | Chart.js 4          |

---

### Project Modules
1. **Admin Login Module** — Secure session-based authentication
2. **Census Registration Module** — 17-field citizen registration form
3. **Citizen Management Module** — Full CRUD: Add / View / Edit / Delete / Search
4. **Census Report Module** — 6 chart types + district-wise tabular report

---

### Quick Setup

#### 1. Install Python (3.8+)
Download from https://python.org

#### 2. Install Flask
```bash
pip install flask
```

#### 3. Run the Application
```bash
cd census_system
python app.py
```

#### 4. Open Browser
```
http://127.0.0.1:5000
```

#### 5. Default Login
| Field    | Value      |
|----------|------------|
| Username | admin      |
| Password | admin@123  |

---

### Project Structure
```
census_system/
├── app.py                  # Flask backend (all routes + DB logic)
├── requirements.txt        # Python dependencies
├── README.md
├── instance/
│   └── census.db           # SQLite database (auto-created on first run)
├── templates/
│   ├── base.html           # Base layout with sidebar & topbar
│   ├── login.html          # Admin login page
│   ├── dashboard.html      # Dashboard with stats & charts
│   ├── add_citizen.html    # Registration form
│   ├── view_citizen.html   # All citizens table
│   ├── update.html         # Edit citizen form
│   ├── search.html         # Search page
│   └── report.html         # Reports & analytics
└── static/
    ├── css/
    │   └── style.css       # Complete design system
    └── js/
        └── main.js         # Sidebar, modals, helpers
```

---

### Flask Routes
| Route              | Method     | Description              |
|--------------------|------------|--------------------------|
| `/`                | GET        | Redirects to login       |
| `/login`           | GET, POST  | Admin authentication     |
| `/logout`          | GET        | Clear session            |
| `/dashboard`       | GET        | Stats & charts           |
| `/add_citizen`     | GET, POST  | Register citizen         |
| `/view_citizen`    | GET        | List all citizens        |
| `/update/<id>`     | GET, POST  | Edit citizen             |
| `/delete/<id>`     | POST       | Delete citizen           |
| `/search`          | GET        | Search citizens          |
| `/report`          | GET        | Analytics & reports      |
| `/api/chart_data`  | GET        | JSON data for charts     |

---

### Database Schema

**admin**
```sql
CREATE TABLE admin (
    admin_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    username  TEXT NOT NULL UNIQUE,
    password  TEXT NOT NULL
);
```

**citizen**
```sql
CREATE TABLE citizen (
    citizen_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    census_id      TEXT NOT NULL UNIQUE,
    name           TEXT NOT NULL,
    father_name    TEXT NOT NULL,
    dob            TEXT NOT NULL,
    age            INTEGER NOT NULL,
    gender         TEXT NOT NULL,
    address        TEXT NOT NULL,
    city           TEXT NOT NULL,
    district       TEXT NOT NULL,
    state          TEXT NOT NULL,
    pincode        TEXT NOT NULL,
    mobile         TEXT NOT NULL,
    email          TEXT,
    education      TEXT NOT NULL,
    occupation     TEXT NOT NULL,
    family_members INTEGER NOT NULL,
    income         REAL NOT NULL,
    created_at     TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

### Features
- ✅ Session-based admin authentication
- ✅ Auto-generated Census ID (CEN000001, CEN000002…)
- ✅ Auto-calculated age from date of birth
- ✅ Client-side JS form validation
- ✅ Mobile number (10-digit) & Pincode (6-digit) validation
- ✅ Responsive sidebar layout (hamburger on mobile)
- ✅ Delete confirmation modal
- ✅ Quick filter on view page
- ✅ 4-field search (name / mobile / census ID / district)
- ✅ 6 visual charts on reports page
- ✅ District-wise tabular report with population share
- ✅ Flash messages with auto-dismiss

---

### Screenshots (after running)
- Login Page: Clean gradient login card
- Dashboard: 6 stat cards + gender donut + district bar chart
- Add Citizen: 3-section form with validation
- View Citizens: Searchable table with edit/delete
- Search: Filter by name, mobile, census ID, district
- Reports: 6 charts (gender, age, district, occupation, education, income)

---

*Developed as a College Level Computer Science Mini Project*
