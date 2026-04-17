import sys
import os
from pathlib import Path

# Adiciona o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from src.infrastructure.job_aggregator import fetch_all_jobs
from dotenv import load_dotenv

load_dotenv()

def test():
    print("Iniciando busca em todas as fontes...")
    jobs = fetch_all_jobs()
    print(f"Busca finalizada. Total de vagas: {len(jobs)}")

if __name__ == "__main__":
    test()
