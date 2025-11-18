import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

# Paste your transcript here
transcript_text = """
Hey, this is Max Kerr. I'm calling from 123 Maple Street in Richmond, Virginia. My air conditioner stopped blowing cold air last night. I think the compressor might be out again. Could I get someone out tomorrow morning if possible? You guys charged me that $89 diagnostic fee last time. Is that still the same? You can reach me at 804-555-2211. And please send Mike again if he's available. Thanks.
"""

print("Extracting structured data...")

response = client.chat.completions.create(
    model="gpt-4o-mini",
    response_format={"type": "json_object"},
    temperature=0,
    messages=[
        {"role": "system", "content": "Extract structured job data in JSON."},
        {"role": "user", "content": f"""
From the following customer call transcript, extract the fields below.

Return ONLY valid JSON.

Fields:
customer_name, phone_number, email, service_address,
job_type, problem_description, urgency, preferred_time,
technician_preference, price_reference, notes

Transcript:
{transcript_text}
"""}
    ]
)

data = response.choices[0].message.content

# 🧾 Save JSON to a file
output_path = "extracted_data.json"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(data)

print(f"\nData extracted and saved to {output_path}!\n")

# Optional: show preview
print(json.dumps(json.loads(data), indent=2))



