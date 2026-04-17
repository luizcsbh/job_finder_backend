import requests
from src.domain.job import Job
from src.infrastructure.cache import cached

URL = "https://www.arbeitnow.com/api/job-board-api"


@cached("arbeitnow")
def fetch_jobs_arbeitnow():
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        jobs = []

        if "data" not in data:
            return []

        for item in data["data"]:
            job = Job(
                title=item["title"],
                company=item["company_name"],
                location=item["location"],
                description=item["description"],
                url=item["url"],
                datate_posted=item.get("created_at", ""),
                category=item.get("tags", []),
                source="ArbeitNow"
            )
            jobs.append(job)

        return jobs
    except Exception as e:
        print(f"Erro ao buscar vagas no ArbeitNow: {e}")
        return []