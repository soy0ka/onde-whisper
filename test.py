# test.py
import requests
import os
import time

def test_full_process():
    # 1. 파일 업로드
    file_path = './sample-0.mp3'
    upload_url = 'http://localhost:4729/upload'
    
    with open(file_path, 'rb') as f:
        files = {
            'file': (file_path, f, 'audio/mp3')
        }
        data = {
            'chunkNumber': '1',
            'totalChunks': '1'
        }
        print("1. 파일 업로드 중...")
        upload_response = requests.post(upload_url, files=files, data=data)
        
    print(f"업로드 상태: {upload_response.status_code}")
    print(f"업로드 응답: {upload_response.json()}")
    
    if upload_response.status_code != 200:
        print("업로드 실패")
        return
        
    file_id = upload_response.json()['fileId']
    
    # 2. Transcribe 요청
    transcribe_url = 'http://localhost:4729/transcribe'
    transcribe_data = {
        "fileId": file_id,
        "callback": "http://localhost:4729/callback",
        "model": "tiny"
    }
    
    print("\n2. 변환 작업 요청 중...")
    transcribe_response = requests.post(transcribe_url, json=transcribe_data)
    print(f"변환 요청 상태: {transcribe_response.status_code}")
    print(f"변환 요청 응답: {transcribe_response.json()}")
    
    if transcribe_response.status_code != 200:
        print("변환 요청 실패")
        return
        
    job_id = transcribe_response.json()['job_id']
    
    # 3. 작업 상태 확인
    status_url = f'http://localhost:4729/job/{job_id}'
    max_retries = 30  # 최대 시도 횟수 증가
    retry_count = 0
    
    print("\n3. 작업 상태 확인 중...")
    while retry_count < max_retries:
        status_response = requests.get(status_url)
        status_data = status_response.json()
        
        print(f"상태 확인 {retry_count + 1}: {status_data.get('status', 'unknown')}")
        
        # 작업이 완료되었거나 실패한 경우
        if status_data.get('status') in ['success', 'failed']:
            print("\n최종 결과:")
            print(status_data)
            break
            
        retry_count += 1
        time.sleep(5)  # 5초 대기
    
    if retry_count >= max_retries:
        print("작업 상태 확인 시간 초과")

    # 4. 모든 작업 목록 확인
    print("\n4. 전체 작업 목록 확인...")
    jobs_response = requests.get('http://localhost:4729/jobs?page=1&per_page=3')
    print(f"작업 목록: {jobs_response.json()}")

if __name__ == "__main__":
    test_full_process()