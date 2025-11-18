# watch_folder.py
# Monitors the folder for new audio files and runs ai_notetaker.py automatically

import os
import time
import subprocess
import sys

print(">>> Using Python:", sys.executable)
FOLDER = os.getcwd()  # current folder
PROCESSED = set()     # keep track of processed files

print("Watching for new audio files... (Press Ctrl+C to stop)")

while True:
    for file in os.listdir(FOLDER):
        if file.endswith((".m4a", ".mp3", ".wav")) and file not in PROCESSED:
            print(f"\nNew file detected: {file}")
            PROCESSED.add(file)

            try:
                #Create a copy of current environment
                env = os.environ.copy()

                #Prepend venv Scripts folder to PATH manually
                venv_path = r"C:\Users\maxke\ai_notetaker\venv\Scripts"
                env["PATH"] = venv_path + os.pathsep + env["PATH"]

                # Run ai_notetaker.py using same interpreter + corrected environment
                subprocess.run(
                    [sys.executable, "ai_notetaker.py"],
                    check=True,
                    env=env
                )

                print(f"Finished processing {file}")

            except Exception as e:
                print(f"Error processing {file}: {e}")

    time.sleep(5)  # check every 5 seconds

