import os
import hashlib
from config.config import ALLOWED_EXTENSIONS

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def merge_chunks(file_id, total_chunks, upload_folder):
    merged_file_path = os.path.join(upload_folder, f"{file_id}")
    
    try:
        with open(merged_file_path, 'wb') as merged_file:
            for chunk_number in range(1, int(total_chunks) + 1):
                chunk_path = os.path.join(upload_folder, f"{file_id}.part{chunk_number}")
                
                if not os.path.exists(chunk_path):
                    raise FileNotFoundError(f"청크 파일이 없습니다: {chunk_path}")
                
                with open(chunk_path, 'rb') as chunk_file:
                    merged_file.write(chunk_file.read())
                
                os.remove(chunk_path)
        
        with open(merged_file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
            
        return {
            "status": "success",
            "merged_file": merged_file_path,
            "file_hash": file_hash
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }