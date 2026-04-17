import os
import requests
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = "linkedin-job-search-api.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}/active-jb-1h"

def test_v2():
    print(f"Testando conexão com novo Host: {RAPIDAPI_HOST}...")
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }
    
    params = {
        "limit": "10",
        "offset": "0",
        "description_type": "text"
    }
    
    try:
        response = requests.get(BASE_URL, headers=headers, params=params, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("Sucesso! Amostra da resposta:")
            data = response.json()
            print(str(data)[:500] + "...")
        else:
            print(f"Erro: {response.text}")
            
    except Exception as e:
        print(f"Exceção: {e}")

if __name__ == "__main__":
    test_v2()
