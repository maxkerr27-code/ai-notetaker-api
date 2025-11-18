import os

# 🔥 ensure psycopg2-binary is installed even if Render ignores requirements.txt
try:
    import psycopg2
except ImportError:
    os.system("pip install psycopg2-binary")
    import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # ---- ensure companies table exists ----
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        api_key TEXT UNIQUE NOT NULL,
        owner_phone TEXT,
        created_at TIMESTAMP NOT NULL
    );
    """)

    # ---- ensure jobs table exists ----
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id SERIAL PRIMARY KEY,
        company_id INTEGER NOT NULL REFERENCES companies(id),
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
        created_at TIMESTAMP NOT NULL,
        transcript_preview TEXT
    );
    """)

    # ---- auto-insert default company if none exist ----
    cursor.execute("SELECT COUNT(*) FROM companies;")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute(
            "INSERT INTO companies (name, api_key, owner_phone, created_at) VALUES (%s, %s, %s, NOW());",
            ("Default Company", "my_twilio_test_key_123", "+12013165908")
        )

    conn.commit()
    conn.close()
    print("DB initialized")
