"""
Jooble API Integration.
Docs: https://jooble.org/api-about
"""
import requests
import os
import json
from src.domain.job import Job
from src.infrastructure.cache import cached

BASE_URL = "http://jooble.org"


@cached("jooble")
def fetch_jobs_jooble():
    """Busca vagas via Jooble API."""
    jooble_key = os.getenv("JOOBLE_API_KEY", "")
    keywords   = os.getenv("KEYWORDS", "developer")
    location   = os.getenv("USER_LOCATION", "Brazil")

    if not jooble_key or jooble_key == "sua_jooble_api_key_aqui":
        print("[Jooble] API key não configurada, pulando.")
        return []

    try:
        url = f"{BASE_URL}/api/{jooble_key}"
        
        # Conforme sugestão do usuário: headers explícitos e payload JSON
        headers = {"Content-type": "application/json"}
        
        # Usamos a primeira keyword da lista para a busca no Jooble
        main_keyword = keywords.split(",")[0] if keywords else "developer"
        
        payload = {
            "keywords": main_keyword,
            "location": location,
            "page": "1"
        }
        
        print(f"[Jooble] Buscando vagas para '{main_keyword}' em '{location}'...")
        
        response = requests.post(
            url, 
            data=json.dumps(payload), 
            headers=headers, 
            timeout=15
        )
        
        if response.status_code == 403:
            print("[Jooble] Erro 403: Acesso negado. Verifique se sua chave API está ativa e registrada.")
            return []
            
        response.raise_for_status()
        data = response.json()

        jobs = []
        for item in data.get("jobs", []):
            job_url = item.get("link", "")
            if not job_url:
                continue

            jobs.append(
                Job(
                    title=item.get("title", "N/A"),
                    company=item.get("company", "N/A"),
                    location=item.get("location", "N/A"),
                    description=item.get("snippet", ""),
                    url=job_url,
                    datate_posted=item.get("publication_date", ""),
                    category=item.get("category", []),
                    source="Jooble"
                )
            )

        return jobs
    except Exception as e:
        print(f"[Jooble] Erro ao buscar vagas: {e}")
        return []
