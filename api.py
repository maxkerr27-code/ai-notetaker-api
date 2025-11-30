from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Form, Request
from fastapi.responses import Response
import uuid
import os
from datetime import datetime
import httpx
import tempfile
from sms import send_sms


from ai_notetaker import process_audio_file
from init_db import create_tables, get_connection   # <-- PostgreSQL only

# -----------------------------------------------------
# INIT APP + DB
# -----------------------------------------------------
app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://leadrescue-frontend.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Ensure tables exist on start
create_tables()

MASTER_API_KEY = os.getenv("MASTER_API_KEY")

# -----------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------
def generate_api_key(name: str) -> str:
    key_suffix = uuid.uuid4().hex[:16]
    return f"{name.lower()}_{key_suffix}"


def get_company_id_from_key(api_key: str):
    if api_key == MASTER_API_KEY:
        return 1

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM companies WHERE api_key = %s", (api_key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


# -----------------------------------------------------
# PROCESS AUDIO FROM URL
# -----------------------------------------------------
@app.post("/process_audio_url")
async def process_audio_url(audio_url: str = Form(...), x_api_key: str = Header(...)):
    company_id = get_company_id_from_key(x_api_key)
    if not company_id:
        raise HTTPException(status_code=401, detail="Invalid API key")

    async with httpx.AsyncClient() as client:
        audio_data = await client.get(audio_url)
        if audio_data.status_code != 200:
            raise HTTPException(status_code=400, detail="Download failed")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_data.content)
        tmp_path = tmp.name

    job_id = process_audio_file(tmp_path, company_id)
    os.remove(tmp_path)
    return {"status": "success", "job_id": job_id, "company_id": company_id}


# -----------------------------------------------------
# TWILIO VOICE
# -----------------------------------------------------
@app.post("/twilio_voice")
async def twilio_voice(request: Request):
    api_key = request.query_params.get("x-api-key")
    xml = f"""
    <Response>
    <Record
        action="https://ai-notetaker-api-1.onrender.com/twilio_recording?x-api-key={api_key}"
            method="POST"
            playBeep="true"
            finishOnKey="#"
        />
        <Say>Thank you. Goodbye.</Say>
    </Response>
    """
    return Response(content=xml, media_type="text/xml")


# -----------------------------------------------------
# TWILIO RECORDING CALLBACK
# -----------------------------------------------------
@app.post("/twilio_recording")
async def twilio_recording(request: Request):
    form = await request.form()
    recording_url = form.get("RecordingUrl")
    if not recording_url:
        return Response("<Response><Say>No RecordingUrl.</Say></Response>", media_type="text/xml")

    api_key = request.query_params.get("x-api-key")
    company_id = get_company_id_from_key(api_key)
    if not company_id:
        return Response("<Response><Say>Invalid API key.</Say></Response>", media_type="text/xml")

    downloadable = recording_url + ".wav"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            downloadable,
            auth=(os.getenv("TWILIO_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        )
    if resp.status_code != 200:
        return Response("<Response><Say>Download failed.</Say></Response>", media_type="text/xml")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(resp.content)
        tmp_path = tmp.name

    job_id = process_audio_file(tmp_path, company_id)
    # 🔥 SMS AFTER JOB IS SAVED
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT owner_phone FROM companies WHERE id = %s", (company_id,))
    result = cursor.fetchone()
    conn.close()

    owner_phone = result[0] if result else None

    if owner_phone:
        print("Triggering SMS notification to owner:", owner_phone)
        send_sms(owner_phone, f"New job saved — ID #{job_id}")
    else:
        print("⚠️ No owner phone stored — skipping SMS")

    return Response(f"<Response><Say>Job saved. ID {job_id}.</Say></Response>", media_type="text/xml")


# -----------------------------------------------------
# REGISTER COMPANY
# -----------------------------------------------------
@app.post("/register_company")
def register_company(name: str):
    api_key = generate_api_key(name)
    created = datetime.now().isoformat(timespec="seconds")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO companies (name, api_key, created_at) VALUES (%s, %s, %s)",
        (name, api_key, created)
    )
    conn.commit()
    conn.close()
    return {"company": name, "api_key": api_key}


# -----------------------------------------------------
# MANUAL FILE UPLOAD
# -----------------------------------------------------
@app.post("/process_audio")
async def process_audio(file: UploadFile = File(...), x_api_key: str = Header(...)):
    company_id = get_company_id_from_key(x_api_key)
    if not company_id:
        raise HTTPException(status_code=401, detail="Invalid API key")

    ext = file.filename.split(".")[-1]
    temp_filename = f"temp_{uuid.uuid4()}.{ext}"
    with open(temp_filename, "wb") as f:
        f.write(await file.read())

    job_id = process_audio_file(temp_filename, company_id)
    os.remove(temp_filename)
    return {"status": "success", "job_id": job_id, "company_id": company_id}


# -----------------------------------------------------
# LOOK UP JOBS
# -----------------------------------------------------
@app.get("/jobs")
def get_jobs(x_api_key: str = Header(...)):
    company_id = get_company_id_from_key(x_api_key)
    if not company_id:
        raise HTTPException(status_code=401, detail="Invalid API key")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE company_id = %s ORDER BY id DESC", (company_id,))
    rows = cursor.fetchall()
    conn.close()
    return {"jobs": rows}


@app.get("/jobs/{job_id}")
def get_job(job_id: int, x_api_key: str = Header(...)):
    company_id = get_company_id_from_key(x_api_key)
    if not company_id:
        raise HTTPException(status_code=401, detail="Invalid API key")

    @app.get("/db_upgrade")
    async def db_upgrade():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                ALTER TABLE companies ADD COLUMN IF NOT EXISTS owner_phone TEXT;
                ALTER TABLE companies ADD COLUMN IF NOT EXISTS owner_email TEXT;
                ALTER TABLE companies ADD COLUMN IF NOT EXISTS notify_sms BOOLEAN DEFAULT TRUE;
            """)
            conn.commit()
            cursor.close()
            conn.close()
            return {"status": "success"}
        except Exception as e:
            return {"error": str(e)}

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = %s AND company_id = %s", (job_id, company_id))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job": row}
