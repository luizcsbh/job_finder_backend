"""
LinkedIn Jobs — via RapidAPI (linkedin-jobs-search by mgujjargamingm / jaypat87).
Host: linkedin-jobs-search.p.rapidapi.com
Endpoint: GET /search_jobs
Docs: https://rapidapi.com/mgujjargamingm/api/linkedin-jobs-search

Requires RAPIDAPI_KEY in .env
"""
import requests
import os
from src.domain.job import Job
from src.infrastructure.cache import cached

RAPIDAPI_KEY  = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = "linkedin-jobs-search.p.rapidapi.com"
BASE_URL      = f"https://{RAPIDAPI_HOST}/search_jobs"

# Palavras-chave e localização configuráveis via .env
KEYWORDS = os.getenv("KEYWORDS", "developer")
LOCATION = os.getenv("USER_LOCATION", "Brazil")

HEADERS = {
    "x-rapidapi-key":  RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST,
}

MAX_PER_KEYWORD = 10   # Máximo de resultados por keyword (respeita o free tier)


@cached("linkedin")
def fetch_jobs_linkedin() -> list[Job]:
    """Busca vagas do LinkedIn via RapidAPI."""
    if not RAPIDAPI_KEY or RAPIDAPI_KEY == "sua_rapidapi_key_aqui":
        print("[LinkedIn/RapidAPI] RAPIDAPI_KEY não configurada, pulando.")
        return []

    keywords_list = [k.strip() for k in KEYWORDS.split(",") if k.strip()]
    all_jobs: list[Job] = []

    # Usa até as primeiras 3 keywords
    for keyword in keywords_list[:3]:
        try:
            params = {
                "keywords": keyword,
                "location": LOCATION,
                "dateSincePosted": "past Week",
                "jobType":         "full time",
                "remoteFilter":    "remote",
                "salary":          "",
                "experienceLevel": "mid-senior level",
                "limit":           str(MAX_PER_KEYWORD),
                "page":            "0",
            }
            response = requests.get(
                BASE_URL,
                headers=HEADERS,
                params=params,
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

            # A resposta é uma lista de vagas diretamente
            items = data if isinstance(data, list) else data.get("jobs", [])

            jobs_fetched = 0
            for item in items:
                url = (
                    item.get("jobUrl")
                    or item.get("url")
                    or item.get("link")
                    or ""
                )
                title = (
                    item.get("title")
                    or item.get("position")
                    or "N/A"
                )
                company = (
                    item.get("company")
                    or item.get("companyName")
                    or "N/A"
                )
                location = (
                    item.get("location")
                    or item.get("place")
                    or LOCATION
                )
                description = (
                    item.get("description")
                    or item.get("snippet")
                    or f"{title} em {company}"
                )

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
                jobs_fetched += 1

            print(f"[LinkedIn/RapidAPI] '{keyword}': {jobs_fetched} vagas")
        except Exception as e:
            print(f"[LinkedIn/RapidAPI] Erro para '{keyword}': {e}")

    # Remove duplicatas por URL
    seen = set()
    unique = []
    for job in all_jobs:
        if job.url not in seen:
            seen.add(job.url)
            unique.append(job)

    print(f"[LinkedIn/RapidAPI] Total único: {len(unique)} vagas")
    return unique
