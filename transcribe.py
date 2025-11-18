# transcribe.py
# Uses OpenAI Whisper to transcribe your voice memo.

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # loads your API key from .env
client = OpenAI()

audio_file = open("sample_call.m4a", "rb")  # make sure this matches your file name

print("Transcribing, please wait...")

transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file
)

print("\nTranscription complete!\n")
print(transcript.text)
