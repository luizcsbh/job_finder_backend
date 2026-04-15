"""
Jooble API — free tier (requires registration for key).
Aggregates jobs from thousands of sites globally.
"""
import requests
import os
from src.domain.job import Job
from src.infrastructure.cache import cached

JOOBLE_KEY = os.getenv("JOOBLE_API_KEY", "")
URL = f"https://jooble.org/api/{JOOBLE_KEY}"


@cached("jooble")
def fetch_jobs_jooble():
    if not JOOBLE_KEY:
        print("Jooble: API key não configurada, pulando.")
        return []

    try:
        payload = {"keywords": "developer", "location": "Brasil", "page": "1"}
        response = requests.post(URL, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()

        jobs = []
        for item in data.get("jobs", []):
            url = item.get("link", "")
            if not url:
                continue

            job = Job(
                title=item.get("title", "N/A"),
                company=item.get("company", "N/A"),
                location=item.get("location", "N/A"),
                description=item.get("snippet", ""),
                url=url,
                source="Jooble"
            )
            jobs.append(job)

        return jobs
    except Exception as e:
        print(f"Erro ao buscar vagas no Jooble: {e}")
        return []
