from fastapi import FastAPI, UploadFile, File, Header, HTTPException
import sqlite3
import init_db
import uuid
import os
import sys
from datetime import datetime    # <-- REQUIRED
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ai_notetaker import process_audio_file
from dotenv import load_dotenv
load_dotenv()

   # your processor

app = FastAPI()
init_db.create_tables()

# -----------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------

def generate_api_key(name: str):
    key_suffix = uuid.uuid4().hex[:16]
    return f"{name.lower()}_{key_suffix}"


def get_company_id_from_key(api_key: str):
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
    cursor.execute(
        "INSERT INTO companies (name, api_key, created_at) VALUES (?, ?, ?)",
        (name, api_key, created)
    )
    conn.commit()
    conn.close()

    return {
        "company_name": name,
        "api_key": api_key,
        "message": "Store this key securely — required to upload audio."
    }


# -----------------------------------------------------
# PROCESS AUDIO ENDPOINT
# -----------------------------------------------------

@app.post("/process_audio")
async def process_audio(file: UploadFile = File(...), x_api_key: str = Header(...)):
    company_id = get_company_id_from_key(x_api_key)
    if not company_id:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")

    # save upload temporarily
    temp_filename = f"temp_{uuid.uuid4()}.wav"
    with open(temp_filename, "wb") as f:
        f.write(await file.read())

    job_id = process_audio_file(temp_filename, company_id)

    os.remove(temp_filename)

    return {"status": "success", "job_id": job_id, "company_id": company_id}


# -----------------------------------------------------
# JOB LOOKUP
# -----------------------------------------------------

@app.get("/jobs")
def get_jobs():
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return {"jobs": rows}


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
