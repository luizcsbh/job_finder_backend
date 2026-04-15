import os
from dotenv import load_dotenv

load_dotenv()

KEYWORDS = os.getenv("KEYWORDS", "").lower().split(",")

def rank_jobs(jobs):
    for job in jobs:
        score = 0
        text = (job.title + job.description).lower()

        for keyword in KEYWORDS:
            if keyword in text:
                score += 1
        
        job.score = score

    return sorted(jobs, key=lambda x: x.score, reverse=True)