import threading
import time
import requests
import mlx_whisper
from config.config import WHISPER_MODELS

def transcribe_audio(speech_file, output_file, callback_url, model, job_id):
    try:
        # 작업 상태를 processing으로 변경
        from app.routes import jobs, JobStatus
        jobs[job_id]["status"] = JobStatus.PROCESSING

        start_time = time.time()

        text_result = mlx_whisper.transcribe(
            speech_file,
            path_or_hf_repo=WHISPER_MODELS[model],
            word_timestamps=True
        )
        text = text_result["text"]

        end_time = time.time()
        execution_time = end_time - start_time

        with open(output_file, "w", encoding="utf-8") as file:
            file.write(text)

        result = {
            "executionTime": execution_time,
            "outputFile": output_file,
            "text": text,
        }

        # 작업 상태를 completed로 변경
        jobs[job_id]["status"] = JobStatus.COMPLETED
        jobs[job_id]["result"] = result

        if callback_url:
            try:
                requests.post(callback_url, json=result)
            except requests.exceptions.RequestException as e:
                print(f"Callback failed: {e}")

    except Exception as e:
        # 에러 발생 시 작업 상태를 failed로 변경
        jobs[job_id]["status"] = JobStatus.FAILED
        jobs[job_id]["error"] = str(e)
        print(f"Transcription failed: {e}")

def process_job(speech_file, output_file, callback_url, model, job_id):
    threading.Thread(
        target=transcribe_audio, 
        args=(speech_file, output_file, callback_url, model, job_id)
    ).start()