import requests
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("JOOBLE_API_KEY", "")
# Testando o host 'api.jooble.org'
URL = f"https://api.jooble.org/api/{key}"

payload = {"keywords": "developer", "location": "Brazil"}
try:
    response = requests.post(URL, json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    print(response.text[:200])
except Exception as e:
    print(f"Erro: {e}")
