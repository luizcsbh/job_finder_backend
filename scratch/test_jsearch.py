import os
import requests
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = "jsearch.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}/search"

def test_jsearch():
    print(f"Testando conexão com JSearch ({RAPIDAPI_HOST})...")
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
    }
    
    # Query mais específica
    params = {
        "query": "Python Developer in Remote",
        "page": "1",
        "num_pages": "1"
    }
    
    try:
        response = requests.get(BASE_URL, headers=headers, params=params, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get("data", [])
            print(f"Encontradas {len(jobs)} vagas.")
            for i, job in enumerate(jobs[:3]):
                print(f"Vaga {i+1}: {job.get('job_title')} - {job.get('employer_name')}")
        else:
            print(f"Erro: {response.text}")
            
    except Exception as e:
        print(f"Exceção: {e}")

if __name__ == "__main__":
    test_jsearch()
