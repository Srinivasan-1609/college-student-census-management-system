from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response
import sqlite3, os, csv, io
from functools import wraps
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT

app = Flask(__name__)
app.secret_key = 'college_census_2024_secret'
DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'census.db')

# ═══════════════════ DATABASE ═══════════════════
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS admin (
            admin_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT NOT NULL UNIQUE,
            password  TEXT NOT NULL,
            full_name TEXT DEFAULT 'Administrator'
        );
        CREATE TABLE IF NOT EXISTS staff (
            staff_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_no   TEXT NOT NULL UNIQUE,
            full_name  TEXT NOT NULL,
            email      TEXT NOT NULL UNIQUE,
            department TEXT NOT NULL,
            designation TEXT NOT NULL,
            mobile     TEXT NOT NULL,
            username   TEXT NOT NULL UNIQUE,
            password   TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS student (
            student_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            census_id      TEXT NOT NULL UNIQUE,
            full_name      TEXT NOT NULL,
            father_name    TEXT NOT NULL,
            mother_name    TEXT NOT NULL,
            dob            TEXT NOT NULL,
            age            INTEGER NOT NULL,
            gender         TEXT NOT NULL,
            blood_group    TEXT,
            address        TEXT NOT NULL,
            city           TEXT NOT NULL,
            district       TEXT NOT NULL,
            state          TEXT NOT NULL,
            pincode        TEXT NOT NULL,
            mobile         TEXT NOT NULL,
            parent_mobile  TEXT NOT NULL,
            email          TEXT,
            department     TEXT NOT NULL,
            course         TEXT NOT NULL,
            year_of_study  INTEGER NOT NULL,
            roll_number    TEXT NOT NULL UNIQUE,
            admission_year INTEGER NOT NULL,
            category       TEXT NOT NULL,
            religion       TEXT,
            nationality    TEXT DEFAULT 'Indian',
            family_income  REAL NOT NULL,
            scholarship    TEXT DEFAULT 'None',
            hostel         TEXT DEFAULT 'Day Scholar',
            transport      TEXT DEFAULT 'Own',
            disability     TEXT DEFAULT 'None',
            s_username     TEXT UNIQUE,
            s_password     TEXT,
            created_at     TEXT DEFAULT CURRENT_TIMESTAMP
        );
        INSERT OR IGNORE INTO admin (username, password, full_name)
            VALUES ('admin', 'admin@123', 'System Administrator');
    ''')
    conn.commit()
    conn.close()

def gen_census_id():
    conn = get_db()
    n = conn.execute('SELECT COUNT(*) as c FROM student').fetchone()['c'] + 1
    conn.close()
    return f'STU{n:06d}'

def gen_staff_no():
    conn = get_db()
    n = conn.execute('SELECT COUNT(*) as c FROM staff').fetchone()['c'] + 1
    conn.close()
    return f'STF{n:04d}'

# ═══════════════════ DECORATORS ═══════════════════
def admin_required(f):
    @wraps(f)
    def d(*a, **kw):
        if 'admin' not in session:
            flash('Admin login required.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*a, **kw)
    return d

def staff_required(f):
    @wraps(f)
    def d(*a, **kw):
        if 'staff_id' not in session and 'admin' not in session:
            flash('Login required.', 'warning')
            return redirect(url_for('staff_login'))
        return f(*a, **kw)
    return d

def student_required(f):
    @wraps(f)
    def d(*a, **kw):
        if 'student_id' not in session:
            flash('Student login required.', 'warning')
            return redirect(url_for('student_login'))
        return f(*a, **kw)
    return d

# ═══════════════════ PUBLIC ═══════════════════
@app.route('/')
def index():
    return render_template('home.html')

# ═══════════════════ STUDENT AUTH ═══════════════════
@app.route('/student/signup', methods=['GET','POST'])
def student_signup():
    if 'student_id' in session:
        return redirect(url_for('student_portal'))
    if request.method == 'POST':
        f = request.form
        census_id = gen_census_id()
        uname = f['s_username'].strip()
        conn = get_db()
        if conn.execute('SELECT 1 FROM student WHERE s_username=?',(uname,)).fetchone():
            conn.close(); flash('Username already taken.','danger')
            return render_template('student_signup.html')
        if conn.execute('SELECT 1 FROM student WHERE roll_number=?',(f['roll_number'].strip(),)).fetchone():
            conn.close(); flash('Roll number already registered.','danger')
            return render_template('student_signup.html')
        try:
            conn.execute('''INSERT INTO student
                (census_id,full_name,father_name,mother_name,dob,age,gender,blood_group,
                 address,city,district,state,pincode,mobile,parent_mobile,email,
                 department,course,year_of_study,roll_number,admission_year,category,
                 religion,nationality,family_income,scholarship,hostel,transport,disability,
                 s_username,s_password)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (census_id, f['full_name'], f['father_name'], f['mother_name'], f['dob'],
                 f['age'], f['gender'], f.get('blood_group',''),
                 f['address'], f['city'], f['district'], f['state'], f['pincode'],
                 f['mobile'], f['parent_mobile'], f.get('email',''),
                 f['department'], f['course'], f['year_of_study'], f['roll_number'],
                 f['admission_year'], f['category'], f.get('religion',''),
                 f.get('nationality','Indian'), f['family_income'],
                 f.get('scholarship','None'), f.get('hostel','Day Scholar'),
                 f.get('transport','Own'), f.get('disability','None'),
                 uname, f['s_password']))
            conn.commit(); conn.close()
            flash(f'Registration successful! Your Student Census ID: {census_id}. Please login.','success')
            return redirect(url_for('student_login'))
        except sqlite3.IntegrityError as e:
            conn.close(); flash(f'Registration error: {e}','danger')
    return render_template('student_signup.html')

@app.route('/student/login', methods=['GET','POST'])
def student_login():
    if 'student_id' in session:
        return redirect(url_for('student_portal'))
    if request.method == 'POST':
        uname = request.form.get('s_username','').strip()
        pw    = request.form.get('s_password','').strip()
        conn  = get_db()
        s = conn.execute('SELECT * FROM student WHERE s_username=? AND s_password=?',(uname,pw)).fetchone()
        conn.close()
        if s:
            session['student_id'] = s['student_id']
            session['student_name'] = s['full_name']
            session['student_roll'] = s['roll_number']
            flash(f'Welcome, {s["full_name"]}!','success')
            return redirect(url_for('student_portal'))
        flash('Invalid username or password.','danger')
    return render_template('student_login.html')

@app.route('/student/logout')
def student_logout():
    session.pop('student_id',None); session.pop('student_name',None); session.pop('student_roll',None)
    flash('Logged out.','info')
    return redirect(url_for('student_login'))

@app.route('/student/portal')
@student_required
def student_portal():
    conn = get_db()
    s = conn.execute('SELECT * FROM student WHERE student_id=?',(session['student_id'],)).fetchone()
    conn.close()
    return render_template('student_portal.html', student=s)

# ═══════════════════ STAFF AUTH ═══════════════════
@app.route('/staff/signup', methods=['GET','POST'])
def staff_signup():
    if request.method == 'POST':
        f = request.form
        staff_no = gen_staff_no()
        uname = f['username'].strip()
        conn = get_db()
        if conn.execute('SELECT 1 FROM staff WHERE username=?',(uname,)).fetchone():
            conn.close(); flash('Username already taken.','danger')
            return render_template('staff_signup.html')
        if conn.execute('SELECT 1 FROM staff WHERE email=?',(f['email'].strip(),)).fetchone():
            conn.close(); flash('Email already registered.','danger')
            return render_template('staff_signup.html')
        try:
            conn.execute('''INSERT INTO staff
                (staff_no,full_name,email,department,designation,mobile,username,password)
                VALUES (?,?,?,?,?,?,?,?)''',
                (staff_no, f['full_name'], f['email'], f['department'],
                 f['designation'], f['mobile'], uname, f['password']))
            conn.commit(); conn.close()
            flash(f'Staff registered! Staff No: {staff_no}. Please login.','success')
            return redirect(url_for('staff_login'))
        except sqlite3.IntegrityError as e:
            conn.close(); flash(f'Error: {e}','danger')
    return render_template('staff_signup.html')

@app.route('/staff/login', methods=['GET','POST'])
def staff_login():
    if 'staff_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        uname = request.form.get('username','').strip()
        pw    = request.form.get('password','').strip()
        conn  = get_db()
        st = conn.execute('SELECT * FROM staff WHERE username=? AND password=?',(uname,pw)).fetchone()
        conn.close()
        if st:
            session['staff_id']   = st['staff_id']
            session['staff_name'] = st['full_name']
            session['staff_dept'] = st['department']
            session['role']       = 'staff'
            flash(f'Welcome, {st["full_name"]}!','success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.','danger')
    return render_template('staff_login.html')

@app.route('/staff/logout')
def staff_logout():
    for k in ['staff_id','staff_name','staff_dept','role']:
        session.pop(k,None)
    flash('Logged out.','info')
    return redirect(url_for('staff_login'))

# ═══════════════════ ADMIN AUTH ═══════════════════
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if 'admin' in session: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        u = request.form.get('username','').strip()
        p = request.form.get('password','').strip()
        conn = get_db()
        a = conn.execute('SELECT * FROM admin WHERE username=? AND password=?',(u,p)).fetchone()
        conn.close()
        if a:
            session['admin'] = u
            session['admin_name'] = a['full_name']
            session['role'] = 'admin'
            flash(f'Welcome, {a["full_name"]}!','success')
            return redirect(url_for('dashboard'))
        flash('Invalid admin credentials.','danger')
    return render_template('admin_login.html')

@app.route('/login', methods=['GET','POST'])
def login():
    return redirect(url_for('admin_login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.','info')
    return redirect(url_for('index'))

# ═══════════════════ DASHBOARD ═══════════════════
@app.route('/dashboard')
@staff_required
def dashboard():
    conn = get_db()
    stats = {
        'total':     conn.execute('SELECT COUNT(*) as c FROM student').fetchone()['c'],
        'male':      conn.execute("SELECT COUNT(*) as c FROM student WHERE gender='Male'").fetchone()['c'],
        'female':    conn.execute("SELECT COUNT(*) as c FROM student WHERE gender='Female'").fetchone()['c'],
        'depts':     conn.execute('SELECT COUNT(DISTINCT department) as c FROM student').fetchone()['c'],
        'avg_income':conn.execute('SELECT ROUND(AVG(family_income),0) as c FROM student').fetchone()['c'] or 0,
        'hostel':    conn.execute("SELECT COUNT(*) as c FROM student WHERE hostel='Hostel'").fetchone()['c'],
        'staff_count':conn.execute('SELECT COUNT(*) as c FROM staff').fetchone()['c'],
        'scholar':   conn.execute("SELECT COUNT(*) as c FROM student WHERE scholarship!='None'").fetchone()['c'],
    }
    recent = conn.execute('SELECT * FROM student ORDER BY student_id DESC LIMIT 6').fetchall()
    dept_data = conn.execute('SELECT department, COUNT(*) as cnt FROM student GROUP BY department ORDER BY cnt DESC').fetchall()
    conn.close()
    return render_template('dashboard.html', stats=stats, recent=recent, dept_data=dept_data)

# ═══════════════════ STUDENT CRUD ═══════════════════
@app.route('/add_student', methods=['GET','POST'])
@staff_required
def add_student():
    if request.method == 'POST':
        f = request.form
        census_id = gen_census_id()
        if get_db().execute('SELECT 1 FROM student WHERE roll_number=?',(f['roll_number'].strip(),)).fetchone():
            flash('Roll number already exists.','danger')
            return render_template('add_student.html')
        try:
            conn = get_db()
            conn.execute('''INSERT INTO student
                (census_id,full_name,father_name,mother_name,dob,age,gender,blood_group,
                 address,city,district,state,pincode,mobile,parent_mobile,email,
                 department,course,year_of_study,roll_number,admission_year,category,
                 religion,nationality,family_income,scholarship,hostel,transport,disability)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (census_id, f['full_name'], f['father_name'], f['mother_name'], f['dob'],
                 f['age'], f['gender'], f.get('blood_group',''),
                 f['address'], f['city'], f['district'], f['state'], f['pincode'],
                 f['mobile'], f['parent_mobile'], f.get('email',''),
                 f['department'], f['course'], f['year_of_study'], f['roll_number'],
                 f['admission_year'], f['category'], f.get('religion',''),
                 f.get('nationality','Indian'), f['family_income'],
                 f.get('scholarship','None'), f.get('hostel','Day Scholar'),
                 f.get('transport','Own'), f.get('disability','None')))
            conn.commit(); conn.close()
            flash(f'Student added! Census ID: {census_id}','success')
            return redirect(url_for('view_students'))
        except sqlite3.IntegrityError as e:
            flash(f'Error: {e}','danger')
    return render_template('add_student.html')

@app.route('/view_students')
@staff_required
def view_students():
    conn = get_db()
    students = conn.execute('SELECT * FROM student ORDER BY student_id DESC').fetchall()
    conn.close()
    return render_template('view_students.html', students=students)

@app.route('/update/<int:sid>', methods=['GET','POST'])
@staff_required
def update(sid):
    conn = get_db()
    s = conn.execute('SELECT * FROM student WHERE student_id=?',(sid,)).fetchone()
    if not s:
        conn.close(); flash('Student not found.','danger')
        return redirect(url_for('view_students'))
    if request.method == 'POST':
        f = request.form
        conn.execute('''UPDATE student SET
            full_name=?,father_name=?,mother_name=?,dob=?,age=?,gender=?,blood_group=?,
            address=?,city=?,district=?,state=?,pincode=?,mobile=?,parent_mobile=?,email=?,
            department=?,course=?,year_of_study=?,roll_number=?,admission_year=?,category=?,
            religion=?,nationality=?,family_income=?,scholarship=?,hostel=?,transport=?,disability=?
            WHERE student_id=?''',
            (f['full_name'],f['father_name'],f['mother_name'],f['dob'],f['age'],f['gender'],
             f.get('blood_group',''),f['address'],f['city'],f['district'],f['state'],f['pincode'],
             f['mobile'],f['parent_mobile'],f.get('email',''),f['department'],f['course'],
             f['year_of_study'],f['roll_number'],f['admission_year'],f['category'],
             f.get('religion',''),f.get('nationality','Indian'),f['family_income'],
             f.get('scholarship','None'),f.get('hostel','Day Scholar'),
             f.get('transport','Own'),f.get('disability','None'),sid))
        conn.commit(); conn.close()
        flash('Student record updated!','success')
        return redirect(url_for('view_students'))
    conn.close()
    return render_template('update_student.html', student=s)

@app.route('/delete/<int:sid>', methods=['POST'])
@staff_required
def delete(sid):
    conn = get_db()
    conn.execute('DELETE FROM student WHERE student_id=?',(sid,))
    conn.commit(); conn.close()
    flash('Student record deleted.','success')
    return redirect(url_for('view_students'))

@app.route('/search')
@staff_required
def search():
    q     = request.args.get('q','').strip()
    field = request.args.get('field','full_name')
    students = []
    if q:
        conn = get_db()
        col_map = {'full_name':'full_name','mobile':'mobile','census_id':'census_id',
                   'department':'department','roll_number':'roll_number','course':'course'}
        col = col_map.get(field,'full_name')
        students = conn.execute(
            f'SELECT * FROM student WHERE {col} LIKE ? ORDER BY student_id DESC',
            (f'%{q}%',)).fetchall()
        conn.close()
    return render_template('search.html', students=students, query=q, field=field)

# ═══════════════════ STAFF MANAGEMENT (Admin only) ═══════════════════
@app.route('/manage_staff')
@admin_required
def manage_staff():
    conn = get_db()
    staff_list = conn.execute('SELECT * FROM staff ORDER BY staff_id DESC').fetchall()
    conn.close()
    return render_template('manage_staff.html', staff_list=staff_list)

@app.route('/delete_staff/<int:sid>', methods=['POST'])
@admin_required
def delete_staff(sid):
    conn = get_db()
    conn.execute('DELETE FROM staff WHERE staff_id=?',(sid,))
    conn.commit(); conn.close()
    flash('Staff record removed.','success')
    return redirect(url_for('manage_staff'))

# ═══════════════════ REPORTS ═══════════════════
@app.route('/report')
@staff_required
def report():
    conn = get_db()
    total    = conn.execute('SELECT COUNT(*) as c FROM student').fetchone()['c']
    male     = conn.execute("SELECT COUNT(*) as c FROM student WHERE gender='Male'").fetchone()['c']
    female   = conn.execute("SELECT COUNT(*) as c FROM student WHERE gender='Female'").fetchone()['c']
    other_g  = conn.execute("SELECT COUNT(*) as c FROM student WHERE gender='Other'").fetchone()['c']
    age_groups = conn.execute('''SELECT
        SUM(CASE WHEN age<18 THEN 1 ELSE 0 END) as minor,
        SUM(CASE WHEN age BETWEEN 18 AND 21 THEN 1 ELSE 0 END) as young,
        SUM(CASE WHEN age BETWEEN 22 AND 25 THEN 1 ELSE 0 END) as mid_age,
        SUM(CASE WHEN age>25 THEN 1 ELSE 0 END) as senior FROM student''').fetchone()
    dept_data   = conn.execute('SELECT department, COUNT(*) as cnt FROM student GROUP BY department ORDER BY cnt DESC').fetchall()
    course_data = conn.execute('SELECT course, COUNT(*) as cnt FROM student GROUP BY course ORDER BY cnt DESC LIMIT 10').fetchall()
    year_data   = conn.execute('SELECT year_of_study, COUNT(*) as cnt FROM student GROUP BY year_of_study ORDER BY year_of_study').fetchall()
    cat_data    = conn.execute('SELECT category, COUNT(*) as cnt FROM student GROUP BY category ORDER BY cnt DESC').fetchall()
    hostel_data = conn.execute('SELECT hostel, COUNT(*) as cnt FROM student GROUP BY hostel').fetchall()
    scholar_data= conn.execute("SELECT scholarship, COUNT(*) as cnt FROM student GROUP BY scholarship ORDER BY cnt DESC").fetchall()
    income_data = conn.execute('''SELECT
        SUM(CASE WHEN family_income<100000 THEN 1 ELSE 0 END) as bpl,
        SUM(CASE WHEN family_income BETWEEN 100000 AND 500000 THEN 1 ELSE 0 END) as mid,
        SUM(CASE WHEN family_income>500000 THEN 1 ELSE 0 END) as high FROM student''').fetchone()
    conn.close()
    return render_template('report.html',
        total=total, male=male, female=female, other_g=other_g,
        age_groups=age_groups, dept_data=dept_data, course_data=course_data,
        year_data=year_data, cat_data=cat_data, hostel_data=hostel_data,
        scholar_data=scholar_data, income_data=income_data)

# ═══════════════════ DOWNLOAD CSV ═══════════════════
@app.route('/download/csv')
@staff_required
def download_csv():
    conn = get_db()
    students = conn.execute('SELECT * FROM student ORDER BY student_id').fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Census ID','Full Name','Father Name','Mother Name','DOB','Age','Gender',
                     'Blood Group','Address','City','District','State','Pincode','Mobile',
                     'Parent Mobile','Email','Department','Course','Year','Roll Number',
                     'Admission Year','Category','Religion','Nationality','Family Income',
                     'Scholarship','Hostel','Transport','Disability','Registered On'])
    for s in students:
        writer.writerow([s['census_id'],s['full_name'],s['father_name'],s['mother_name'],
                         s['dob'],s['age'],s['gender'],s['blood_group'] or '',
                         s['address'],s['city'],s['district'],s['state'],s['pincode'],
                         s['mobile'],s['parent_mobile'],s['email'] or '',
                         s['department'],s['course'],s['year_of_study'],s['roll_number'],
                         s['admission_year'],s['category'],s['religion'] or '',
                         s['nationality'],s['family_income'],s['scholarship'],
                         s['hostel'],s['transport'],s['disability'],s['created_at']])
    now = datetime.now().strftime('%Y%m%d_%H%M')
    return Response(output.getvalue(), mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=student_census_{now}.csv'})

# ═══════════════════ DOWNLOAD PDF ═══════════════════
@app.route('/download/pdf')
@staff_required
def download_pdf():
    conn = get_db()
    students = conn.execute('SELECT * FROM student ORDER BY student_id').fetchall()
    stats = {
        'total':  conn.execute('SELECT COUNT(*) as c FROM student').fetchone()['c'],
        'male':   conn.execute("SELECT COUNT(*) as c FROM student WHERE gender='Male'").fetchone()['c'],
        'female': conn.execute("SELECT COUNT(*) as c FROM student WHERE gender='Female'").fetchone()['c'],
        'depts':  conn.execute('SELECT COUNT(DISTINCT department) as c FROM student').fetchone()['c'],
    }
    conn.close()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'],
                                 fontSize=18, textColor=colors.HexColor('#1d4ed8'),
                                 spaceAfter=4, alignment=TA_CENTER)
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'],
                               fontSize=10, textColor=colors.HexColor('#64748b'),
                               spaceAfter=14, alignment=TA_CENTER)
    stat_style = ParagraphStyle('Stat', parent=styles['Normal'],
                                fontSize=9, textColor=colors.HexColor('#374151'))

    elements = []
    elements.append(Paragraph('College Student Census Management System', title_style))
    elements.append(Paragraph(f'Student Census Report — Generated on {datetime.now().strftime("%d %B %Y, %I:%M %p")}', sub_style))
    elements.append(HRFlowable(width='100%', thickness=1.5, color=colors.HexColor('#3b82f6'), spaceAfter=10))

    # Summary row
    sum_data = [['Total Students','Male','Female','Departments'],
                [str(stats['total']), str(stats['male']), str(stats['female']), str(stats['depts'])]]
    sum_table = Table(sum_data, colWidths=[6*cm]*4)
    sum_table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1d4ed8')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,0),10),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('BACKGROUND',(0,1),(-1,1),colors.HexColor('#eff6ff')),
        ('FONTNAME',(0,1),(-1,1),'Helvetica-Bold'),
        ('FONTSIZE',(0,1),(-1,1),14),
        ('ROWBACKGROUNDS',(0,1),(-1,1),[colors.HexColor('#eff6ff')]),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#bfdbfe')),
        ('TOPPADDING',(0,0),(-1,-1),8),
        ('BOTTOMPADDING',(0,0),(-1,-1),8),
    ]))
    elements.append(sum_table)
    elements.append(Spacer(1, 14))

    # Student table
    headers = ['#','Census ID','Name','Roll No','Dept','Course','Yr','Gender','DOB','Mobile','Category','Hostel','Income']
    data = [headers]
    for i, s in enumerate(students, 1):
        data.append([
            str(i), s['census_id'], s['full_name'][:20],
            s['roll_number'], s['department'][:12], s['course'][:14],
            str(s['year_of_study']), s['gender'], s['dob'],
            s['mobile'], s['category'],
            s['hostel'], f"₹{int(s['family_income']):,}"
        ])

    col_w = [0.7*cm, 2.2*cm, 3.8*cm, 2.2*cm, 2.5*cm, 3*cm,
             0.8*cm, 1.5*cm, 2*cm, 2.4*cm, 1.6*cm, 2.2*cm, 2.2*cm]
    t = Table(data, colWidths=col_w, repeatRows=1)
    row_colors = []
    for i in range(1, len(data)):
        bg = colors.HexColor('#f0f9ff') if i % 2 == 0 else colors.white
        row_colors.append(('BACKGROUND',(0,i),(-1,i),bg))
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,0),8),
        ('FONTSIZE',(0,1),(-1,-1),7.5),
        ('FONTNAME',(0,1),(-1,-1),'Helvetica'),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#cbd5e1')),
        ('TOPPADDING',(0,0),(-1,-1),5),
        ('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, colors.HexColor('#f8fafc')]),
    ] + row_colors))
    elements.append(t)
    elements.append(Spacer(1,10))
    elements.append(Paragraph(f'Report generated by College Census Management System | Total records: {stats["total"]}', sub_style))

    doc.build(elements)
    buf.seek(0)
    now = datetime.now().strftime('%Y%m%d_%H%M')
    return Response(buf.read(), mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=student_census_{now}.pdf'})

# ═══════════════════ DOWNLOAD DEPT CSV ═══════════════════
@app.route('/download/csv/<dept>')
@staff_required
def download_dept_csv(dept):
    conn = get_db()
    students = conn.execute('SELECT * FROM student WHERE department=? ORDER BY roll_number',(dept,)).fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Census ID','Name','Roll No','Course','Year','Gender','DOB','Mobile','Category','Family Income','Scholarship','Hostel'])
    for s in students:
        writer.writerow([s['census_id'],s['full_name'],s['roll_number'],s['course'],s['year_of_study'],
                         s['gender'],s['dob'],s['mobile'],s['category'],s['family_income'],s['scholarship'],s['hostel']])
    fname = dept.replace(' ','_')
    return Response(output.getvalue(), mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={fname}_census.csv'})

# ═══════════════════ API ═══════════════════
@app.route('/api/chart_data')
@staff_required
def chart_data():
    conn = get_db()
    dept_rows  = conn.execute('SELECT department, COUNT(*) as cnt FROM student GROUP BY department ORDER BY cnt DESC LIMIT 8').fetchall()
    course_rows= conn.execute('SELECT course, COUNT(*) as cnt FROM student GROUP BY course ORDER BY cnt DESC LIMIT 8').fetchall()
    conn.close()
    return jsonify({
        'departments': {'labels':[r['department'] for r in dept_rows], 'data':[r['cnt'] for r in dept_rows]},
        'courses':     {'labels':[r['course']     for r in course_rows],'data':[r['cnt'] for r in course_rows]},
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
