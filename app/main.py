from fastapi import FastAPI, File, UploadFile
import subprocess
import os
from pathlib import Path

UPLOAD_DIR = Path("app/uploads")
WHISPER_CLI = "./whisper.cpp/main"
MODEL = "models/ggml-base.en.bin"


UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI()

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".wav"):
        return {"error": "Only .wav files are supported."}

    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as f:
        f.write(await file.read())

    output_path = file_path.with_suffix(".txt")

    # Run whisper.cpp
    try:
        subprocess.run([
            WHISPER_CLI,
            "-m", MODEL,
            "-f", str(file_path),
            "-of", str(output_path).replace(".txt", "")
        ], check=True)
    except subprocess.CalledProcessError:
        return {"error": "Transcription failed."}

    with open(output_path, "r") as f:
        transcript = f.read()

    return {"filename": file.filename, "transcript": transcript}
