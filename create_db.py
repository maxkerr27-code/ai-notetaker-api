import sqlite3

conn = sqlite3.connect("jobs.db")
cursor = conn.cursor()

# Companies table (multi-tenant)
cursor.execute("""
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    api_key TEXT UNIQUE,
    created_at TEXT
);
""")

# Jobs table
cursor.execute("""
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER,
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
    FOREIGN KEY(company_id) REFERENCES companies(id)
);
""")

conn.commit()
conn.close()

print("Database created with multi-tenant support.")

