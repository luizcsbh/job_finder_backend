import requests
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("JOOBLE_API_KEY", "")
URL = f"https://jooble.org/api/{key}"

headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

payload = {"keywords": "developer", "location": "Brazil"}
try:
    response = requests.post(URL, json=payload, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    print(response.text[:200])
except Exception as e:
    print(f"Erro: {e}")
