import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "medications.db")
VALID_DAY_TYPES = {"everyday", "weekdays", "weekends"}

def init_db():
    """Initialize the database with medications table."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dosage TEXT NOT NULL,
            reminder_times TEXT NOT NULL,
            day_type TEXT NOT NULL DEFAULT 'everyday',
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute("PRAGMA table_info(medications)")
    medication_columns = {row[1] for row in cursor.fetchall()}
    if "day_type" not in medication_columns:
        cursor.execute("ALTER TABLE medications ADD COLUMN day_type TEXT NOT NULL DEFAULT 'everyday'")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medication_id INTEGER NOT NULL,
            reminder_time TEXT NOT NULL,
            reminder_date TEXT,
            taken INTEGER DEFAULT 0,
            taken_at TIMESTAMP,
            FOREIGN KEY (medication_id) REFERENCES medications (id)
        )
    ''')

    # Backfill schema for existing databases.
    cursor.execute("PRAGMA table_info(reminders)")
    reminder_columns = {row[1] for row in cursor.fetchall()}
    if "reminder_date" not in reminder_columns:
        cursor.execute("ALTER TABLE reminders ADD COLUMN reminder_date TEXT")

    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_reminders_unique_slot
        ON reminders (medication_id, reminder_time, reminder_date)
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medication_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            username TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (medication_id) REFERENCES medications (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def _normalize_day_type(day_type):
    value = (day_type or "everyday").strip().lower()
    if value not in VALID_DAY_TYPES:
        raise ValueError("day_type must be one of: everyday, weekdays, weekends")
    return value


def _normalize_reminder_times(reminder_times):
    normalized = []
    for time_str in (reminder_times or "").split(","):
        slot = time_str.strip()
        if not slot:
            continue
        parsed = datetime.strptime(slot, "%H:%M")
        normalized.append(parsed.strftime("%H:%M"))

    if not normalized:
        raise ValueError("At least one valid reminder time (HH:MM) is required")

    return ",".join(normalized)


def add_medication(name, dosage, reminder_times, day_type="everyday"):
    """Add a new medication.
    
    Args:
        name: Medication name (e.g., "Aspirin")
        dosage: Dosage (e.g., "500mg")
        reminder_times: Comma-separated times in HH:MM format (e.g., "08:00,14:00,20:00")
        day_type: One of everyday, weekdays, weekends
    """
    normalized_day_type = _normalize_day_type(day_type)
    normalized_times = _normalize_reminder_times(reminder_times)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO medications (name, dosage, reminder_times, day_type)
        VALUES (?, ?, ?, ?)
    ''', (name, dosage, normalized_times, normalized_day_type))
    
    conn.commit()
    med_id = cursor.lastrowid
    conn.close()
    
    return med_id

def get_all_medications():
    """Get all active medications."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, dosage, reminder_times FROM medications WHERE active = 1
    ''')
    
    meds = cursor.fetchall()
    conn.close()
    
    return meds


def get_all_medications_for_admin():
    """Get all active medications including day type for admin UI."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, dosage, reminder_times, day_type
        FROM medications
        WHERE active = 1
        ORDER BY name
    ''')

    meds = cursor.fetchall()
    conn.close()

    return meds


def remove_medication(medication_id):
    """Soft-delete a medication and remove pending reminder rows."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE medications
        SET active = 0
        WHERE id = ?
    ''', (medication_id,))

    cursor.execute('''
        DELETE FROM reminders
        WHERE medication_id = ?
          AND taken = 0
    ''', (medication_id,))

    conn.commit()
    conn.close()


def update_medication_times(medication_id, reminder_times):
    """Update reminder times for a medication."""
    normalized_times = _normalize_reminder_times(reminder_times)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE medications
        SET reminder_times = ?
        WHERE id = ?
    ''', (normalized_times, medication_id))

    cursor.execute('''
        DELETE FROM reminders
        WHERE medication_id = ?
          AND taken = 0
    ''', (medication_id,))

    conn.commit()
    conn.close()


def log_medication_action(medication_id, action, old_value=None, new_value=None, username="system"):
    """Log a medication action."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO logs (medication_id, action, old_value, new_value, username)
        VALUES (?, ?, ?, ?, ?)
    ''', (medication_id, action, old_value, new_value, username))

    conn.commit()
    conn.close()


def get_medication_logs(limit=50):
    """Get recent medication logs."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            l.id,
            m.name,
            l.action,
            l.old_value,
            l.new_value,
            l.username,
            l.created_at
        FROM logs l
        JOIN medications m ON m.id = l.medication_id
        ORDER BY l.created_at DESC
        LIMIT ?
    ''', (limit,))

    logs = cursor.fetchall()
    conn.close()

    return logs

def mark_reminder_taken(medication_id, reminder_time):
    """Mark a reminder as taken."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE reminders
        SET taken = 1, taken_at = CURRENT_TIMESTAMP
        WHERE medication_id = ?
          AND reminder_time = ?
          AND reminder_date = DATE('now')
    ''', (medication_id, reminder_time))
    
    conn.commit()
    conn.close()


def mark_reminder_taken_by_id(reminder_id):
    """Mark a reminder row as taken by reminder id."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE reminders
        SET taken = 1, taken_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (reminder_id,))

    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()

    return updated


def _parse_reminder_times(reminder_times):
    """Split and normalize comma-separated HH:MM values."""
    return [time_str.strip() for time_str in reminder_times.split(',') if time_str.strip()]


def _is_medication_due_on_date(day_type, dt_obj):
    """Return True if medication should run on the given date."""
    try:
        normalized = _normalize_day_type(day_type)
    except ValueError:
        normalized = "everyday"
    weekday_index = dt_obj.weekday()  # Monday=0, Sunday=6

    if normalized == "everyday":
        return True
    if normalized == "weekdays":
        return weekday_index < 5
    return weekday_index >= 5


def sync_today_reminders(today=None):
    """Ensure one reminder row exists per medication/time for the current day."""
    if today is None:
        target_date = datetime.now()
    else:
        target_date = datetime.strptime(today, "%Y-%m-%d")

    today = target_date.strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, reminder_times, day_type
        FROM medications
        WHERE active = 1
    ''')
    medications = cursor.fetchall()

    for medication_id, reminder_times, day_type in medications:
        if not _is_medication_due_on_date(day_type, target_date):
            continue
        for reminder_time in _parse_reminder_times(reminder_times):
            cursor.execute('''
                INSERT OR IGNORE INTO reminders (medication_id, reminder_time, reminder_date, taken)
                VALUES (?, ?, ?, 0)
            ''', (medication_id, reminder_time, today))

    conn.commit()
    conn.close()


def get_today_reminders_with_status(now_dt=None):
    """Return all today's reminders with computed status for UI display."""
    if now_dt is None:
        now_dt = datetime.now()

    today = now_dt.strftime("%Y-%m-%d")
    current_time = now_dt.strftime("%H:%M")

    sync_today_reminders(today=today)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            r.id,
            m.id,
            m.name,
            m.dosage,
            r.reminder_time,
                        r.taken
        FROM reminders r
        JOIN medications m ON m.id = r.medication_id
        WHERE m.active = 1
          AND r.reminder_date = ?
        ORDER BY r.reminder_time, m.name
    ''', (today,))

    rows = cursor.fetchall()
    conn.close()

    reminders = []
    for reminder_id, medication_id, name, dosage, reminder_time, taken in rows:
        is_due = reminder_time <= current_time
        status = "medicine taken" if taken else "medicine to be taken"
        reminders.append({
            "reminder_id": reminder_id,
            "medication_id": medication_id,
            "name": name,
            "dosage": dosage,
            "reminder_time": reminder_time,
            "taken": bool(taken),
            "due": is_due,
            "status": status,
        })

    return reminders


def is_today_reminder_taken(medication_id, reminder_time, today=None):
    """Check if a medication/time reminder for today is already marked as taken."""
    if today is None:
        today = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT taken
        FROM reminders
        WHERE medication_id = ?
          AND reminder_time = ?
          AND reminder_date = ?
        LIMIT 1
    ''', (medication_id, reminder_time, today))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return False
    return bool(row[0])

def get_pending_reminders():
    """Get all pending reminders for today."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.id, m.name, m.dosage, m.reminder_times
        FROM medications m
        WHERE m.active = 1
    ''')
    
    meds = cursor.fetchall()
    conn.close()
    
    return meds


def get_medicines_taken_by_date(limit_days=30):
    """Get medicines grouped by reminder date for the last N days.

    Returns a list of dicts with:
    - date: formatted date string (e.g., "Jun 17")
    - count: number of reminder rows on that day
    - medicines: list of medicine names on that day
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            r.reminder_date,
            m.name,
            COUNT(*) as count
        FROM reminders r
        JOIN medications m ON m.id = r.medication_id
        WHERE r.reminder_date IS NOT NULL
        GROUP BY r.reminder_date, m.name
        ORDER BY r.reminder_date DESC
        LIMIT ?
    ''', (limit_days * 10,))  # Get up to 10x limit_days rows to ensure we have enough dates
    
    rows = cursor.fetchall()
    conn.close()
    
    # Group by date
    date_map = {}
    for reminder_date, med_name, count in rows:
        if reminder_date not in date_map:
            date_map[reminder_date] = {
                'date': reminder_date,
                'medicines': [],
                'count': 0
            }
        date_map[reminder_date]['medicines'].append(med_name)
        date_map[reminder_date]['count'] += count
    
    # Sort by date descending and limit to limit_days
    result = sorted(date_map.values(), key=lambda x: x['date'], reverse=True)[:limit_days]
    
    # Format the date for display
    for item in result:
        try:
            date_obj = datetime.strptime(item['date'], '%Y-%m-%d')
            item['date_display'] = date_obj.strftime('%b %d')  # e.g., "Jun 17"
        except:
            item['date_display'] = item['date']
    
    return result
