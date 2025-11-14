import sqlite3

conn = sqlite3.connect("jobs.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    api_key TEXT UNIQUE NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    customer_name TEXT,
    phone_number TEXT,
    email TEXT,
    service_address TEXT,
    job_type TEXT,
    problem_description TEXT,
    urgency TEXT,
    preferred_time TEXT,
    technician_preference TEXT,
    price_reference TEXT,
    notes TEXT,
    audio_file TEXT,
    created_at TEXT,
    transcript_preview TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
)
""")

conn.commit()
conn.close()
print("DB initialized")
