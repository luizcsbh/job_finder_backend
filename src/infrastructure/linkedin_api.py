"""
LinkedIn Jobs — via RapidAPI (linkedin-job-search-api).
Host: linkedin-job-search-api.p.rapidapi.com
Endpoint: GET /active-jb-1h
"""
import requests
import os
from src.domain.job import Job
from src.infrastructure.cache import cached

RAPIDAPI_KEY  = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = "linkedin-job-search-api.p.rapidapi.com"
BASE_URL      = f"https://{RAPIDAPI_HOST}/active-jb-1h"

# Localização configurável via .env
LOCATION = os.getenv("USER_LOCATION", "Brazil")

HEADERS = {
    "x-rapidapi-key":  RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST,
    "Content-Type": "application/json"
}

MAX_RESULTS = 100


@cached("linkedin")
def fetch_jobs_linkedin() -> list[Job]:
    """Busca vagas do LinkedIn via RapidAPI (linkedin-job-search-api)."""
    if not RAPIDAPI_KEY or RAPIDAPI_KEY == "sua_rapidapi_key_aqui":
        print("[LinkedIn/RapidAPI] RAPIDAPI_KEY não configurada, pulando.")
        return []

    all_jobs: list[Job] = []

    try:
        # Parâmetros conforme documentação fornecida pelo usuário
        params = {
            "limit": str(MAX_RESULTS),
            "offset": "0",
            "description_type": "text"
        }
        
        print(f"[LinkedIn/RapidAPI] Buscando vagas em {RAPIDAPI_HOST}...")
        
        response = requests.get(
            BASE_URL,
            headers=HEADERS,
            params=params,
            timeout=20,
        )
        
        if response.status_code == 401:
            print("[LinkedIn/RapidAPI] Erro 401: Endpoint desativado para sua assinatura ou chave inválida.")
            return []
            
        response.raise_for_status()
        data = response.json()

        # A estrutura costuma ser uma lista diretamente ou dentro de 'jobs'/'data'
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("jobs") or data.get("data") or data.get("results") or []

        for item in items:
            # Mapeamento flexível de campos para diferentes versões da API
            url = item.get("job_link") or item.get("url") or item.get("jobUrl") or ""
            title = item.get("job_title") or item.get("title") or "N/A"
            company = item.get("company_name") or item.get("company") or "N/A"
            location = item.get("job_location") or item.get("location") or LOCATION
            description = item.get("job_description") or item.get("description") or f"{title} em {company}"

            if not url or title == "N/A":
                continue

            all_jobs.append(
                Job(
                    title=title,
                    company=company,
                    location=location,
                    description=description,
                    url=url,
                    source="LinkedIn",
                )
            )

    except Exception as e:
        print(f"[LinkedIn/RapidAPI] Erro ao buscar: {e}")

    # Remove duplicatas por URL
    seen = set()
    unique = []
    for job in all_jobs:
        if job.url not in seen:
            seen.add(job.url)
            unique.append(job)

    print(f"[LinkedIn/RapidAPI] Total único: {len(unique)} vagas")
    return unique
