"""
The Muse API — free, no key required.
Docs: https://www.themuse.com/developers/api/v2
Returns tech and professional jobs globally.
"""
import requests
from src.domain.job import Job
from src.infrastructure.cache import cached

URL = "https://www.themuse.com/api/public/jobs?page=1&descending=true"


@cached("themuse")
def fetch_jobs_themuse():
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        jobs = []
        for item in data.get("results", []):
            company = item.get("company", {}).get("name", "N/A")
            locations = item.get("locations", [])
            location = locations[0].get("name", "Remote") if locations else "Remote"
            refs = item.get("refs", {})
            url = refs.get("landing_page", "")
            if not url:
                continue

            job = Job(
                title=item.get("name", "N/A"),
                company=company,
                location=locations,
                description=item.get("contents", ""),
                url=url,
                datate_posted=item.get("publication_date", ""),
                category=item.get("categories", []),
                source="The Muse"
            )
            jobs.append(job)

        return jobs
    except Exception as e:
        print(f"Erro ao buscar vagas no The Muse: {e}")
        return []
