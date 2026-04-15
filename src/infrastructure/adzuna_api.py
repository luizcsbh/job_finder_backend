"""
Adzuna API — free tier available (requires registration for key).
Uses public job listings from RSS / open API pattern.
Note: Free tier via https://api.adzuna.com/v1/api/jobs/{country}/search/{page}
We use software category with no key as a fallback (or key via env).
"""
import requests
import os
from src.domain.job import Job
from src.infrastructure.cache import cached

APP_ID = os.getenv("ADZUNA_APP_ID", "")
APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
URL = "https://api.adzuna.com/v1/api/jobs/br/search/1"


@cached("adzuna")
def fetch_jobs_adzuna():
    if not APP_ID or not APP_KEY:
        print("Adzuna: APP_ID ou APP_KEY não configurados, pulando.")
        return []

    try:
        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "results_per_page": 50,
            "what": "developer",
            "content-type": "application/json"
        }
        response = requests.get(URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        jobs = []
        for item in data.get("results", []):
            url = item.get("redirect_url", "")
            if not url:
                continue

            job = Job(
                title=item.get("title", "N/A"),
                company=item.get("company", {}).get("display_name", "N/A"),
                location=item.get("location", {}).get("display_name", "N/A"),
                description=item.get("description", ""),
                url=url,
                source="Adzuna"
            )
            jobs.append(job)

        return jobs
    except Exception as e:
        print(f"Erro ao buscar vagas no Adzuna: {e}")
        return []
