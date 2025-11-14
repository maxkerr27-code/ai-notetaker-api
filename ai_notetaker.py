# ai_notetaker.py
# Provides function process_audio_file for API — does NOT auto-run on import.

import os
import json
import sqlite3
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_TRANSCRIBE = "whisper-1"
MODEL_EXTRACT = "gpt-4o-mini"


def process_audio_file(audio_path: str, company_id: int):
    """
    Full workflow: transcribe → extract fields → insert into SQLite
    Returns job_id.
    """
    print(f"[processor] Processing audio for company {company_id}: {audio_path}")

    # 1. TRANSCRIBE
    with open(audio_path, "rb") as audio:
        transcript = client.audio.transcriptions.create(
            model=MODEL_TRANSCRIBE,
            file=audio
        )
    text = transcript.text
    print("[processor] Transcription complete.")

    # 2. EXTRACT DATA
    extract_prompt = f"""
    Extract structured JSON fields from this call transcript:

    customer_name
    phone_number
    email
    service_address
    job_type
    problem_description
    urgency
    preferred_time
    technician_preference
    price_reference
    notes

    Transcript:
    {text}
    """

    print("[processor] Extracting structured fields...")
    response = client.chat.completions.create(
        model=MODEL_EXTRACT,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "Extract structured job data in JSON."},
            {"role": "user", "content": extract_prompt}
        ]
    )

    data = json.loads(response.choices[0].message.content)
    print("[processor] Extraction complete.")

    # 3. SAVE TO SQLITE
    created_at = datetime.now().isoformat(timespec="seconds")
    transcript_preview = text[:200]
    filename = os.path.basename(audio_path)

    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO jobs (
            company_id,
            customer_name,
            phone_number,
            email,
            service_address,
            job_type,
            problem_description,
            urgency,
            preferred_time,
            technician_preference,
            price_reference,
            notes,
            audio_file,
            created_at,
            transcript_preview
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        company_id,
        data.get("customer_name"),
        data.get("phone_number"),
        data.get("email"),
        data.get("service_address"),
        data.get("job_type"),
        data.get("problem_description"),
        data.get("urgency"),
        data.get("preferred_time"),
        data.get("technician_preference"),
        data.get("price_reference"),
        data.get("notes"),
        filename,
        created_at,
        transcript_preview
    ))

    job_id = cursor.lastrowid
    conn.commit()
    conn.close()

    print(f"[processor] Job inserted to database. job_id={job_id}")
    return job_id


# IMPORTANT — DO NOT AUTO-RUN ANYTHING WHEN IMPORTED
if __name__ == "__main__":
    print("Standalone test mode — not used by API deployment.")
    # OPTIONAL TEST:
    # process_audio_file("sample_call.m4a", company_id=1)
