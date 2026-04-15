from src.infrastructure.remotive_api import fetch_jobs
from src.application.matcher import rank_jobs
from src.utils.logger import log


def main():
    log("Buscando vagas...")
    jobs = fetch_jobs()

    log(f"{len(jobs)} vagas encontradas")

    ranked_jobs = rank_jobs(jobs)

    log("Top 10 vagas recomendadas:\n")

    for job in ranked_jobs[:10]:
        print(f"""
Título: {job.title}
Empresa: {job.company}
Score: {job.score}
Link: {job.url}
-------------------------
        """)


if __name__ == "__main__":
    main()