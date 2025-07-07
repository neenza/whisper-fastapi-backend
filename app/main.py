from fastapi import FastAPI, File, UploadFile
import subprocess
import os
from pathlib import Path
import shutil

UPLOAD_DIR = Path("app/uploads")
WHISPER_CLI = "whisper"
MODEL = "models/ggml-base.en.bin"


UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI()

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    # Accept any audio file
    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Convert to wav if needed
    if not file.filename.lower().endswith(".wav"):
        wav_path = file_path.with_suffix(".wav")
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", str(file_path), str(wav_path)
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            return {"error": f"Failed to convert to wav: {e}"}
        try:
            file_path.unlink()
        except Exception:
            pass
        file_path = wav_path

    # Always re-encode to mono, 16kHz for whisper.cpp
    reencoded_path = file_path.with_name(file_path.stem + "_mono16k.wav")
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", str(file_path), "-ac", "1", "-ar", "16000", str(reencoded_path)
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        return {"error": f"Failed to re-encode to mono/16kHz: {e}"}
    try:
        if file_path != reencoded_path:
            file_path.unlink()
    except Exception:
        pass
    file_path = reencoded_path

    output_path = file_path.with_suffix(".txt")

    # Run whisper.cpp
    try:
        subprocess.run([
            WHISPER_CLI,
            "-m", MODEL,
            "-f", str(file_path),
            "-otxt",
            "-of", str(output_path).replace(".txt", "")
        ], check=True)
    except subprocess.CalledProcessError as e:
        return {"error": f"Transcription failed: {e}"}

    with open(output_path, "r") as f:
        transcript = f.read()

    return {"filename": file.filename, "transcript": transcript}
