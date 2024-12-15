# app/routes.py
from flask import Blueprint, request, jsonify
import os
import uuid
from config.config import UPLOAD_FOLDER, WHISPER_MODELS
from app.services import process_job
from app.utils import allowed_file, merge_chunks
from app.database import Database
from datetime import datetime

api = Blueprint('api', __name__)
db = Database()

@api.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "파일이 없습니다."}), 400
    
    chunk = request.files['file']
    chunk_number = request.form.get('chunkNumber', '1')
    total_chunks = request.form.get('totalChunks', '1')
    file_id = request.form.get('fileId')
    
    if not allowed_file(chunk.filename):
        return jsonify({
            "status": "error",
            "message": "지원하지 않는 파일 형식입니다."
        }), 400

    if chunk_number == '1' and not file_id:
        file_id = str(uuid.uuid4())
    
    if not file_id:
        return jsonify({
            "status": "error",
            "message": "파일 ID가 제공되지 않았습니다."
        }), 400

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # 청크 파일 저장
    chunk_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.part{chunk_number}")
    chunk.save(chunk_path)
    
    # 마지막 청크인 경우 파일 병합
    if int(chunk_number) == int(total_chunks):
        merge_result = merge_chunks(file_id, total_chunks, UPLOAD_FOLDER)
        
        if merge_result["status"] == "error":
            return jsonify({
                "status": "error",
                "message": merge_result["message"]
            }), 400
            
        db.save_file(file_id, chunk.filename, merge_result["merged_file"])
        return jsonify({
            "status": "success",
            "fileId": file_id,
            "message": "파일이 성공적으로 업로드되었습니다.",
            "file_hash": merge_result["file_hash"]
        })
    
    return jsonify({
        "status": "success",
        "fileId": file_id,
        "message": f"청크 {chunk_number}/{total_chunks} 업로드 완료"
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

        file = db.get_file(file_id)
        if not file:
            return jsonify({
                "status": "error",
                "message": "파일을 찾을 수 없습니다."
            }), 404

        # job_id를 먼저 생성
        job_id = str(uuid.uuid4())
        output_file = os.path.join(UPLOAD_FOLDER, f"{job_id}.txt")

        # 작업 시작 시간과 함께 작업 저장
        db.save_job(job_id, file_id, model, callback_url, started_at=datetime.now())
        
        # 작업 처리 시작
        process_job(file['file_path'], output_file, callback_url, model, job_id)

        return jsonify({
            "job_id": job_id,
            "status": "success",
            "message": "작업이 성공적으로 등록되었습니다."
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    job = db.get_job(job_id)
    
    print(job)
    if not job:
        return jsonify({
            "status": "error",
            "message": "작업을 찾을 수 없습니다."
        }), 404
    
    return jsonify({
        "status": "success",
        "job": job
    })

@api.route('/jobs', methods=['GET'])
def get_all_jobs():
    jobs = db.get_all_jobs()
    return jsonify({
        "status": "success",
        "jobs": jobs if jobs else []
    })