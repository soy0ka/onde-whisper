# app/database.py
import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_file="whisper.db"):
        self.db_file = db_file
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        c = conn.cursor()

        # 파일 정보를 저장하는 테이블
        c.execute('''
            CREATE TABLE IF NOT EXISTS files (
                file_id TEXT PRIMARY KEY,
                original_filename TEXT,
                file_path TEXT,
                created_at TIMESTAMP
            )
        ''')

        # 작업 정보를 저장하는 테이블
        c.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                file_id TEXT,
                status TEXT,
                model TEXT,
                callback_url TEXT,
                created_at TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                result TEXT,
                error TEXT,
                FOREIGN KEY (file_id) REFERENCES files (file_id)
            )
        ''')

        conn.commit()
        conn.close()

    def get_file(self, file_id):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM files WHERE file_id = ?', (file_id,))
        file = c.fetchone()
        conn.close()

        if file:
            return dict(file)  # sqlite3.Row를 dictionary로 변환
        return None

    def save_file(self, file_id, original_filename, file_path):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO files (file_id, original_filename, file_path, created_at)
            VALUES (?, ?, ?, ?)
        ''', (file_id, original_filename, file_path, datetime.now()))
        conn.commit()
        conn.close()

    def save_job(self, job_id, file_id, model, callback_url):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO jobs (job_id, file_id, status, model, callback_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (job_id, file_id, 'pending', model, callback_url, datetime.now()))
        conn.commit()
        conn.close()

    def update_job_status(self, job_id, status, result=None, error=None):
        conn = self.get_connection()
        c = conn.cursor()

        updates = {'status': status}
        if status == 'processing':
            updates['started_at'] = datetime.now()
        elif status in ['completed', 'failed']:
            updates['completed_at'] = datetime.now()

        if result:
            updates['result'] = json.dumps(result)
        if error:
            updates['error'] = str(error)

        set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
        values = list
        
    def get_job(self, job_id):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM jobs WHERE job_id = ?', (job_id,))
        job = c.fetchone()
        conn.close()
        
        if job:
            job_dict = dict(job)
            # JSON 문자열로 저장된 result를 파이썬 객체로 변환
            if job_dict.get('result'):
                try:
                    job_dict['result'] = json.loads(job_dict['result'])
                except json.JSONDecodeError:
                    job_dict['result'] = None
            return job_dict
        return None
      
    def get_all_jobs(self):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM jobs')
        jobs = c.fetchall()
        conn.close()
        
        job_list = []
        for job in jobs:
            job_dict = dict(job)
            # JSON 문자열로 저장된 result를 파이썬 객체로 변환
            if job_dict.get('result'):
                try:
                    job_dict['result'] = json.loads(job_dict['result'])
                except json.JSONDecodeError:
                    job_dict['result'] = None
            job_list.append(job_dict)
        return job_list
