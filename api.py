from fastapi import FastAPI, UploadFile, File, Header, HTTPException
import sqlite3
import init_db
import uuid
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))   # <-- add this
from ai_notetaker import process_audio_file
   # your existing processor

app = FastAPI()

# -----------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------

def generate_api_key(name: str):
    key_suffix = uuid.uuid4().hex[:16]
    return f"{name.lower()}_{key_suffix}"


def get_company_id_from_key(api_key: str):
    """Look up a company ID from its API key."""
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM companies WHERE api_key = ?", (api_key,))
    row = cursor.fetchone()

    conn.close()
    return row[0] if row else None


# -----------------------------------------------------
# REGISTER A NEW COMPANY
# -----------------------------------------------------

@app.post("/register_company")
def register_company(name: str):
    api_key = generate_api_key(name)
    created = datetime.now().isoformat(timespec="seconds")

    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO companies (name, api_key, created_at)
        VALUES (?, ?, ?)
    """, (name, api_key, created))

    conn.commit()
    conn.close()

    return {
        "company_name": name,
        "api_key": api_key,
        "message": "Store this API key securely — it identifies your company."
    }


# -----------------------------------------------------
# PROCESS AUDIO ENDPOINT (SECURED)
# -----------------------------------------------------

@app.post("/process_audio")
async def process_audio(
    file: UploadFile = File(...),
    x_api_key: str = Header(...)
):
    # 1. Validate API key
    company_id = get_company_id_from_key(x_api_key)
    if not company_id:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")

    # 2. Save uploaded audio file temporarily
    temp_filename = f"temp_{uuid.uuid4()}.wav"
    with open(temp_filename, "wb") as f:
        f.write(await file.read())

    # 3. Process audio (your local engine)
    job_id = process_audio_file(temp_filename, company_id)

    # 4. Clean up
    os.remove(temp_filename)

    return {
        "status": "success",
        "job_id": job_id,
        "company_id": company_id
    }


# -----------------------------------------------------
# GET ALL JOBS (for debugging)
# -----------------------------------------------------

@app.get("/jobs")
def get_jobs():
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM jobs ORDER BY id DESC")
    rows = cursor.fetchall()

    conn.close()
    return {"jobs": rows}


# -----------------------------------------------------
# GET A SINGLE JOB
# -----------------------------------------------------

@app.get("/jobs/{job_id}")
def get_job(job_id: int):
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()

    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"job": row}
