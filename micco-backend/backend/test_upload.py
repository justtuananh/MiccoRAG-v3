import requests
import sys

file_path = r"C:\Users\tuana\Downloads\01_Kien_Truc_Transformer.docx"
url = "http://localhost:8000/api/v1/documents/upload/1"

try:
    with open(file_path, 'rb') as f:
        print(f"Uploading {file_path}...")
        files = {'file': (file_path.split('\\')[-1], f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
        response = requests.post(url, files=files)
        
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
