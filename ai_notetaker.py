# ai_notetaker.py
import json
import sqlite3
from datetime import datetime
from openai import OpenAI

client = OpenAI()
MODEL_TRANSCRIBE = "whisper-1"
MODEL_EXTRACT = "gpt-4o-mini"


def process_audio_file(audio_path: str, company_id: int):
    """
    Transcribe + extract data + store in DB → return job_id
    """
    print("Transcribing call...")
    with open(audio_path, "rb") as audio:
        transcript = client.audio.transcriptions.create(
            model=MODEL_TRANSCRIBE,
            file=audio
        )
    text = transcript.text

    print("Extracting structured data…")
    extraction = client.chat.completions.create(
        model=MODEL_EXTRACT,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system",
             "content": "Extract structured job fields as JSON."},
            {"role": "user", "content": text}
        ],
    )
    data = json.loads(extraction.choices[0].message.content)

    created_at = datetime.now().isoformat(timespec="seconds")
    transcript_preview = text[:200]

    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    cursor.execute(
        """
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
            created_at,
            transcript_preview
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
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
            created_at,
            transcript_preview,
        ),
    )

    job_id = cursor.lastrowid
    conn.commit()
    conn.close()

    print("Saved job →", job_id)
    return job_id
