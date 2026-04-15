import os
import re
from pypdf import PdfReader

def extract_text_from_pdf(path):
    if not os.path.exists(path):
        return ""

    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Erro ao ler PDF: {e}")
        return ""

def determine_career_info(text):
    skills_db = {
        "Frontend": ["React", "Vue", "Angular", "HTML", "CSS", "JavaScript", "TypeScript", "Tailwind", "Next.js", "SASS", "Redux"],
        "Backend": ["Python", "Node.js", "Java", "PHP", "Go", "Ruby", "Express", "Django", "FastAPI", "Spring", "Laravel", "C#", ".NET"],
        "Database": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "SQL", "Oracle", "Cassandra"],
        "DevOps": ["Docker", "Kubernetes", "AWS", "Azure", "GCP", "CI/CD", "Linux", "Git", "Terraform", "Jenkins"],
        "Mobile": ["React Native", "Flutter", "Swift", "Kotlin", "iOS", "Android"],
        "Data Science": ["Pandas", "NumPy", "TensorFlow", "PyTorch", "Scikit-Learn", "R", "SQL", "Spark"]
    }

    found_skills = {}
    keywords = []
    text_lower = text.lower()

    category_scores = {cat: 0 for cat in skills_db.keys()}
    
    for category, skills in skills_db.items():
        matched = []
        for s in skills:
            if re.search(r'\b' + re.escape(s.lower()) + r'\b', text_lower):
                matched.append(s)
                keywords.append(s)
                category_scores[category] += 1
        if matched:
            found_skills[category] = matched

    roles = {
        "Software Engineer": ["engineer", "developer", "desenvolvedor", "engenheiro", "programmer"],
        "Project Manager": ["manager", "gestor", "lead", "product", "agile", "scrum"],
        "Data Scientist": ["data", "cientista", "analyst", "analista"],
        "DevOps Engineer": ["devops", "cloud", "infrastructure", "sre"],
        "Designer": ["designer", "ux", "ui", "layout"]
    }

    focus_role = ""
    max_role_score = 0
    for role, terms in roles.items():
        score = sum(1 for term in terms if term in text_lower)
        if score > max_role_score:
            max_role_score = score
            focus_role = role

    top_stack = max(category_scores, key=category_scores.get) if any(category_scores.values()) else ""
    
    if focus_role and top_stack:
        focus = f"{focus_role} ({top_stack})"
    elif focus_role:
        focus = focus_role
    elif top_stack:
        focus = f"{top_stack} Specialist"
    else:
        focus = "Professional"

    total_matches = sum(category_scores.values())
    if total_matches > 15:
        seniority = "Senior"
    elif total_matches > 7:
        seniority = "Pleno"
    else:
        seniority = "Júnior"

    completeness = 20
    if focus_role: completeness += 30
    if len(keywords) > 5: completeness += 25
    if len(found_skills.keys()) >= 3: completeness += 25

    return {
        "skills": found_skills,
        "keywords": list(set(keywords)),
        "focus": focus,
        "scores": category_scores,
        "metrics": {
            "seniority": seniority,
            "completeness": completeness,
            "readiness": min(total_matches * 5, 100),
            "diversity": len(found_skills.keys())
        }
    }