"""
JSearch API — via RapidAPI (covers LinkedIn and others).
Host: jsearch.p.rapidapi.com
Endpoint: GET /search
"""
import requests
import os
from src.domain.job import Job
from src.infrastructure.cache import cached

RAPIDAPI_KEY  = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = "jsearch.p.rapidapi.com"
BASE_URL      = f"https://{RAPIDAPI_HOST}/search"

# Configurações via .env
KEYWORDS = os.getenv("KEYWORDS", "developer")
LOCATION = os.getenv("USER_LOCATION", "Brazil")

HEADERS = {
    "x-rapidapi-key":  RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST,
}


@cached("linkedin")
def fetch_jobs_linkedin() -> list[Job]:
    """Busca vagas via JSearch API (inclui LinkedIn e múltiplos boards)."""
    if not RAPIDAPI_KEY or RAPIDAPI_KEY == "sua_rapidapi_key_aqui":
        print("[JSearch/RapidAPI] RAPIDAPI_KEY não configurada, pulando.")
        return []

    all_jobs: list[Job] = []
    
    # Criamos uma query combinada
    query = f"{KEYWORDS} in {LOCATION}"

    try:
        params = {
            "query": query,
            "page": "1",
            "num_pages": "1",
            "date_posted": "all",
            "remote_jobs_only": "true" # Opcional: foca em vagas remotas
        }
        
        print(f"[JSearch/RapidAPI] Buscando: '{query}'...")
        
        response = requests.get(
            BASE_URL,
            headers=HEADERS,
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
