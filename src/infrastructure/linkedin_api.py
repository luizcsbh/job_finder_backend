"""
JSearch API — via RapidAPI (covers LinkedIn and others).
Host: jsearch.p.rapidapi.com
Endpoint: GET /search
"""
import requests
import os
from src.domain.job import Job
from src.infrastructure.cache import cached

RAPIDAPI_HOST = "jsearch.p.rapidapi.com"
BASE_URL      = f"https://{RAPIDAPI_HOST}/search"


@cached("linkedin")
def fetch_jobs_linkedin() -> list[Job]:
    """Busca vagas via JSearch API (inclui LinkedIn e múltiplos boards)."""
    # Fetch env vars inside function to ensure they are loaded after load_dotenv()
    rapid_key = os.getenv("RAPIDAPI_KEY", "")
    keywords  = os.getenv("KEYWORDS", "developer")
    location  = os.getenv("USER_LOCATION", "Brazil")

    if not rapid_key or rapid_key == "sua_rapidapi_key_aqui":
        print("[JSearch/RapidAPI] RAPIDAPI_KEY não configurada, pulando.")
        return []

    all_jobs: list[Job] = []
    
    # Criamos uma query combinada
    query = f"{keywords} in {location}"

    try:
        headers = {
            "x-rapidapi-key":  rapid_key,
            "x-rapidapi-host": RAPIDAPI_HOST,
        }
        
        params = {
            "query": query,
            "page": "1",
            "num_pages": "1",
            "date_posted": "all",
            "remote_jobs_only": "true"
        }
        
        print(f"[JSearch/RapidAPI] Buscando: '{query}'...")
        
        response = requests.get(
            BASE_URL,
            headers=headers,
            params=params,
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        items = data.get("data", [])

        for item in items:
            url = item.get("job_apply_link") or item.get("job_google_link") or ""
            title = item.get("job_title") or "N/A"
            company = item.get("employer_name") or "N/A"
            location = f"{item.get('job_city', '')}, {item.get('job_country', '')}".strip(", ") or LOCATION
            description = item.get("job_description") or f"{title} em {company}"

            if not url or title == "N/A":
                continue

            all_jobs.append(
                Job(
                    title=title,
                    company=company,
                    location=location,
                    description=description,
                    url=url,
                    datate_posted=item.get("job_posted_at_datetime_utc", ""),
                    salary=salary,
                    salaryCurrency=salaryCurrency, # pyright: ignore[reportUndefinedVariable]
                    category=item.get("job_category", ""),
                    source="LinkedIn/JSearch",
                )
            )

    except Exception as e:
        print(f"[JSearch/RapidAPI] Erro ao buscar: {e}")

    # Remove duplicatas por URL
    seen = set()
    unique = []
    for job in all_jobs:
        if job.url not in seen:
            seen.add(job.url)
            unique.append(job)

    print(f"[JSearch/RapidAPI] Total único: {len(unique)} vagas")
    return unique
