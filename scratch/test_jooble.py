import os
import requests
from dotenv import load_dotenv

load_dotenv()

JOOBLE_KEY = os.getenv("JOOBLE_API_KEY", "")
URL = f"https://jooble.org/api/{JOOBLE_KEY}"

def test_jooble():
    print(f"Testando conexão com Jooble (Key: {'Configurada' if JOOBLE_KEY else 'NÃO CONFIGURADA'})...")
    if not JOOBLE_KEY:
        return

    payload = {"keywords": "software engineer", "location": "Brazil"}
    try:
        response = requests.post(URL, json=payload, timeout=15)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            jobs = data.get("jobs", [])
            print(f"Encontradas {len(jobs)} vagas.")
            if jobs:
                print(f"Amostra: {jobs[0].get('title')} em {jobs[0].get('company')}")
        else:
            print(f"Erro: {response.text}")
    except Exception as e:
        print(f"Exceção: {e}")

if __name__ == "__main__":
    test_jooble()
