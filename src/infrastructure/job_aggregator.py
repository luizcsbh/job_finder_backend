from concurrent.futures import ThreadPoolExecutor, as_completed
from src.infrastructure.remotive_api import fetch_jobs
from src.infrastructure.arbeitnow_api import fetch_jobs_arbeitnow
from src.infrastructure.themuse_api import fetch_jobs_themuse
from src.infrastructure.jobicecream_api import fetch_jobs_jobicecream
from src.infrastructure.jooble_api import fetch_jobs_jooble
from src.infrastructure.linkedin_api import fetch_jobs_linkedin


ALL_SOURCES = [
    fetch_jobs,             # Remotive
    fetch_jobs_arbeitnow,  # ArbeitNow
    fetch_jobs_themuse,    # The Muse
    fetch_jobs_jobicecream, # JobIceCream
    fetch_jobs_jooble,     # Jooble (requires env key)
    fetch_jobs_linkedin,   # LinkedIn (public scraping)
]


def fetch_all_jobs():
    jobs = []
    with ThreadPoolExecutor(max_workers=len(ALL_SOURCES)) as executor:
        futures = {executor.submit(fn): fn.__name__ for fn in ALL_SOURCES}
        for future in as_completed(futures):
            source_name = futures[future]
            try:
                result = future.result()
                jobs.extend(result)
                print(f"[Aggregator] {source_name}: {len(result)} vagas carregadas")
            except Exception as e:
                print(f"[Aggregator] Erro em {source_name}: {e}")

    print(f"[Aggregator] Total: {len(jobs)} vagas de {len(ALL_SOURCES)} fontes")
    return jobs