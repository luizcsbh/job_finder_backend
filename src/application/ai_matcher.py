from sentence_transformers import SentenceTransformer, util


def calculate_ai_scores(resume_text, jobs):
    model = SentenceTransformer('all-MiniLM-L6-v2')

    texts = [resume_text] + [f"{job.title} {job.description}" for job in jobs]
    embeddings = model.encode(texts)

    resume_embedding = embeddings[0]
    job_embeddings = embeddings[1:]

    similarities = util.cos_sim(resume_embedding, job_embeddings)[0]

    for i, job in enumerate(jobs):
        job.ai_score = round(similarities[i].item() * 100, 2)

    return jobs