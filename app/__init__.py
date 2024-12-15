from flask import Flask
from app.routes import api
from config.config import MAX_FILE_SIZE, UPLOAD_FOLDER

def create_app():
    app = Flask(__name__)
    
    # 추가 설정
    app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    
    # 블루프린트 등록
    app.register_blueprint(api)
    
    return app