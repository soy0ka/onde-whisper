from flask import Blueprint, request, jsonify
import os
import uuid
from config.config import UPLOAD_FOLDER, WHISPER_MODELS
from app.services import process_job
from app.utils import allowed_file, merge_chunks
from datetime import datetime

api = Blueprint('api', __name__)

class JobStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# 진행 중인 작업을 저장할 딕셔너리
jobs = {}

@api.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "파일이 없습니다."}), 400
    
    chunk = request.files['file']
    chunk_number = request.form.get('chunkNumber', '1')
    total_chunks = request.form.get('totalChunks', '1')
    file_id = request.form.get('fileId')
    
    print(f"Received file: {chunk.filename}")  # 디버깅용
    print(f"Chunk number: {chunk_number}")
    print(f"Total chunks: {total_chunks}")
    print(f"File ID: {file_id}")
    
    if not allowed_file(chunk.filename):
        return jsonify({
            "status": "error",
            "message": "지원하지 않는 파일 형식입니다."
        }), 400

    # 첫 번째 청크일 때 새로운 file_id 생성
    if chunk_number == '1' and not file_id:
        file_id = str(uuid.uuid4())
    
    if not file_id:
        return jsonify({
            "status": "error",
            "message": "파일 ID가 제공되지 않았습니다."
        }), 400

    # UPLOAD_FOLDER가 존재하는지 확인하고 없으면 생성
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # 파일 저장 경로
    file_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.part{chunk_number}")
    print(f"Saving file to: {file_path}")  # 디버깅용
    
    # 파일 저장
    chunk.save(file_path)
    
    # 마지막 청크인 경우 파일 병합
    if int(chunk_number) == int(total_chunks):
        try:
            merge_result = merge_chunks(file_id, total_chunks, UPLOAD_FOLDER)
            print(f"Merge result: {merge_result}")  # 디버깅용
            return jsonify({
                "status": "success",
                "fileId": file_id,
                "message": "파일이 성공적으로 업로드되었습니다."
            })
        except Exception as e:
            print(f"Error merging chunks: {str(e)}")  # 디버깅용
            return jsonify({
                "status": "error",
                "message": f"파일 병합 중 오류 발생: {str(e)}"
            }), 500
    
    return jsonify({
        "status": "success",
        "fileId": file_id
    })

@api.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        request_body = request.get_json()
        file_id = request_body["fileId"]
        callback_url = request_body["callback"]
        model = request_body.get("model", "turbo")
        
        if model not in WHISPER_MODELS:
            return jsonify({
                "status": "error",
                "message": f"지원하지 않는 모델입니다. 사용 가능한 모델: {', '.join(WHISPER_MODELS.keys())}"
            }), 400

        job_id = str(uuid.uuid4())
        output_file = os.path.join(UPLOAD_FOLDER, f"{job_id}.txt")

        # 작업 상태 저장
        jobs[job_id] = {
            "status": JobStatus.PENDING,
            "file_id": file_id,
            "model": model,
            "callback_url": callback_url,
            "created_at": datetime.now(),
            "output_file": output_file
        }

        process_job(os.path.join(UPLOAD_FOLDER, f"{file_id}"), output_file, callback_url, model, job_id)

        return jsonify({
            "job_id": job_id,
            "status": "success",
            "message": "작업이 성공적으로 등록되었습니다."
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
      
@api.route('/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    if job_id not in jobs:
        return jsonify({
            "status": "error",
            "message": "작업을 찾을 수 없습니다."
        }), 404

    job = jobs[job_id]
    
    if job["status"] == JobStatus.COMPLETED:
        with open(job["output_file"], 'r') as f:
            result = f.read()
            
        return jsonify({
            "status": "success",
            "job_id": job_id,
            "job_status": job["status"],
            "result": result
        })
    
    return jsonify({
        "status": "success",
        "job_id": job_id,
        "job_status": job["status"]
    })

@api.route('/files', methods=['GET'])
def get_uploaded_files():
    files = os.listdir(UPLOAD_FOLDER)
    return jsonify({"uploaded_files": files})

@api.route('/jobs', methods=['GET'])
def get_all_jobs():
    return jsonify({
        "status": "success",
        "jobs": jobs
    })