import os
import requests
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = "linkedin-job-search-api.p.rapidapi.com"

endpoints = ["/active-jb-1h", "/search", "/jobs", "/search-jobs"]

def test_endpoints():
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
    }
    
    for ep in endpoints:
        url = f"https://{RAPIDAPI_HOST}{ep}"
        print(f"Testando {url}...")
        try:
            response = requests.get(url, headers=headers, params={"limit": 5}, timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"SUCESSO em {ep}!")
                return
        except:
            pass

if __name__ == "__main__":
    test_endpoints()
