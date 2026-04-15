from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calculate_ai_scores(resume_text, jobs):
    documents = [resume_text]

    for job in jobs:
        documents.append(f"{job.title} {job.description}")

    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)

    resume_vector = tfidf_matrix[0]

    for i, job in enumerate(jobs):
        job_vector = tfidf_matrix[i + 1]

        similarity = cosine_similarity(resume_vector, job_vector)[0][0]
        job.ai_score = round(similarity * 100, 2)

    return jobs