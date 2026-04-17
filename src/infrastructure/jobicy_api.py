"""
Jobicy API — free, no key required.
Docs: https://jobicy.com/jobs-api
Aggregates remote jobs from multiple sources.
"""
import requests
from src.domain.job import Job
from src.infrastructure.cache import cached

# Correct URL for Jobicy API
URL = "https://jobicy.com/api/v2/remote-jobs"


@cached("jobicy")
def fetch_jobs_jobicy():
    try:
        print(f"[Jobicy] Buscando vagas em {URL}...")
        response = requests.get(URL, timeout=15, headers={"Accept": "application/json"})
        response.raise_for_status()
        data = response.json()

        jobs = []
        # Jobicy returns data in a 'jobs' key
        items = data.get("jobs", [])

        for item in items:
            url = item.get("url") or item.get("job_url") or ""
            if not url:
                continue

            jobs.append(
                Job(
                    title=item.get("jobTitle", "N/A"),
                    company=item.get("companyName", "N/A"),
                    location=item.get("jobGeo", "Remote"),
                    description=item.get("jobExcerpt", ""),
                    url=url,
                    datate_posted=item.get("jobPostedAt", ""),
                    category=item.get("jobCategory", ""),
                    source="Jobicy"
                )
            )

        return jobs
    except Exception as e:
        print(f"[Jobicy] Erro ao buscar vagas: {e}")
        return []
