import sys
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = "linkedin-jobs-search.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}/search_jobs"

def test_direct():
    print(f"Testando conexão direta com RapidAPI ({RAPIDAPI_HOST})...")
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
    }
    
    params = {
        "keywords": "python",
        "location": "Brazil",
        "limit": "2"
    }
    
    try:
        print(f"Headers: {headers}")
        response = requests.get(BASE_URL, headers=headers, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Erro: {response.text}")
        else:
            print("Sucesso! Resposta:")
            print(response.json())
            
    except Exception as e:
        print(f"Exceção: {e}")

if __name__ == "__main__":
    if not RAPIDAPI_KEY or RAPIDAPI_KEY == "sua_rapidapi_key_aqui":
        print("ERRO: RAPIDAPI_KEY não configurada no .env")
    else:
        test_direct()
