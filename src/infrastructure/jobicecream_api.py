"""
JobIceCream API — free, no key required.
Docs: https://jobicecream.com/
Aggregates remote jobs from multiple sources.
"""
import requests
from src.domain.job import Job
from src.infrastructure.cache import cached

URL = "https://jobicecream.com/api/jobs?page=1"


@cached("jobicecream")
def fetch_jobs_jobicecream():
    try:
        response = requests.get(URL, timeout=10, headers={"Accept": "application/json"})
        response.raise_for_status()
        data = response.json()

        jobs = []
        items = data if isinstance(data, list) else data.get("jobs", data.get("data", []))

        for item in items:
            url = item.get("url") or item.get("apply_url") or item.get("link", "")
            if not url:
                continue

            job = Job(
                title=item.get("title", "N/A"),
                company=item.get("company", "N/A"),
                location=item.get("location", "Remote"),
                description=item.get("description", ""),
                url=url,
                source="JobIceCream"
            )
            jobs.append(job)

        return jobs
    except Exception as e:
        print(f"Erro ao buscar vagas no JobIceCream: {e}")
        return []
