# app/services.py
import threading
import time
import requests
import mlx_whisper
from config.config import WHISPER_MODELS
from app.database import Database

db = Database()

def transcribe_audio(speech_file, output_file, callback_url, model, job_id):
    try:
        db.update_job_status(job_id, 'processing')
        
        start_time = time.time()
        text_result = mlx_whisper.transcribe(
            speech_file,
            path_or_hf_repo=WHISPER_MODELS[model],
            word_timestamps=True
        )
        text = text_result["text"]
        end_time = time.time()
        
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(text)

        result = {
            "executionTime": end_time - start_time,
            "outputFile": output_file,
            "text": text,
        }

        db.update_job_status(job_id, 'completed', result=result)

        if callback_url:
            try:
                requests.post(callback_url, json=result)
            except requests.exceptions.RequestException as e:
                print(f"Callback failed: {e}")

    except Exception as e:
        db.update_job_status(job_id, 'failed', error=str(e))
        print(f"Transcription failed: {e}")

def process_job(speech_file, output_file, callback_url, model, job_id):
    threading.Thread(
        target=transcribe_audio, 
        args=(speech_file, output_file, callback_url, model, job_id)
    ).start()