import sqlite3
from datetime import datetime, date
from pathlib import Path

DB_PATH = Path(__file__).parent / "vdart_progress.db"

def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            target_days INTEGER NOT NULL,
            daily_minutes INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            total_sessions INTEGER DEFAULT 0,
            total_score REAL DEFAULT 0,
            streak INTEGER DEFAULT 0,
            last_session_date TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            session_number INTEGER,
            scenario TEXT,
            score REAL,
            duration_minutes INTEGER,
            messages_count INTEGER,
            session_date TEXT,
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            session_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp TEXT,
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
    """)
    conn.commit()
    conn.close()

def create_employee(name, role, target_days, daily_minutes):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO employees (name,role,target_days,daily_minutes,created_at) VALUES (?,?,?,?,?)",
              (name, role, target_days, daily_minutes, datetime.now().isoformat()))
    eid = c.lastrowid
    conn.commit(); conn.close()
    return eid

def get_employee(eid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE id=?", (eid,))
    row = c.fetchone(); conn.close()
    if not row: return None
    cols = ["id","name","role","target_days","daily_minutes","created_at","total_sessions","total_score","streak","last_session_date"]
    return dict(zip(cols, row))

def get_all_employees():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id,name,role,total_sessions,streak FROM employees ORDER BY id DESC")
    rows = c.fetchall(); conn.close()
    return [{"id":r[0],"name":r[1],"role":r[2],"sessions":r[3],"streak":r[4]} for r in rows]

def start_session(employee_id, scenario):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT total_sessions FROM employees WHERE id=?", (employee_id,))
    row = c.fetchone()
    session_number = (row[0] or 0) + 1
    c.execute("INSERT INTO sessions (employee_id,session_number,scenario,session_date) VALUES (?,?,?,?)",
              (employee_id, session_number, scenario, datetime.now().isoformat()))
    sid = c.lastrowid
    conn.commit(); conn.close()
    return sid

def end_session(employee_id, session_id, score, duration_minutes, messages_count):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE sessions SET score=?,duration_minutes=?,messages_count=? WHERE id=?",
              (score, duration_minutes, messages_count, session_id))
    c.execute("SELECT total_sessions,total_score,streak,last_session_date FROM employees WHERE id=?", (employee_id,))
    row = c.fetchone()
    total_sessions = (row[0] or 0) + 1
    total_score = (row[1] or 0) + score
    streak = row[2] or 0
    last_date = row[3]
    today = date.today().isoformat()
    if last_date == today:
        pass
    elif last_date and (date.today() - date.fromisoformat(last_date)).days == 1:
        streak += 1
    else:
        streak = 1
    c.execute("UPDATE employees SET total_sessions=?,total_score=?,streak=?,last_session_date=? WHERE id=?",
              (total_sessions, total_score, streak, today, employee_id))
    conn.commit(); conn.close()

def save_message(employee_id, session_id, role, content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO chat_history (employee_id,session_id,role,content,timestamp) VALUES (?,?,?,?,?)",
              (employee_id, session_id, role, content, datetime.now().isoformat()))
    conn.commit(); conn.close()

def get_session_history(employee_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT session_number,scenario,score,duration_minutes,messages_count,session_date,id
                 FROM sessions WHERE employee_id=? ORDER BY session_number DESC LIMIT 15""", (employee_id,))
    rows = c.fetchall(); conn.close()
    return [{"session":r[0],"scenario":r[1],"score":r[2],"duration":r[3],"messages":r[4],"date":r[5],"id":r[6]} for r in rows]

def get_session_messages(session_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role,content,timestamp FROM chat_history WHERE session_id=? ORDER BY id ASC", (session_id,))
    rows = c.fetchall(); conn.close()
    return [{"role":r[0],"content":r[1],"timestamp":r[2]} for r in rows]

def get_avg_score(employee_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT AVG(score) FROM sessions WHERE employee_id=? AND score IS NOT NULL", (employee_id,))
    result = c.fetchone()[0]; conn.close()
    return round(result or 0, 1)
