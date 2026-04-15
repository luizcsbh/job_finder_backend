import requests
from src.domain.job import Job
from src.infrastructure.cache import cached

API_URL = "https://remotive.com/api/remote-jobs"

@cached("remotive")
def fetch_jobs():
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        jobs = []

        if "jobs" not in data:
            return []

        for item in data["jobs"]:
            job = Job(
                title=item["title"],
                company=item["company_name"],
                location=item["candidate_required_location"],
                description=item["description"],
                url=item["url"],
                source="Remotive"
            )
            jobs.append(job)

        return jobs
    except Exception as e:
        print(f"Erro ao buscar vagas no Remotive: {e}")
        return []