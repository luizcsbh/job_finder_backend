class Job:
    def __init__(self, title, company, location, description, url, source, datate_posted=None, category=None, salary=None):
        self.title = title
        self.company = company
        self.location = location
        self.description = description
        self.url = url
        self.source = source
        self.score = 0
        self.ai_score = 0
        self.datate_posted = datate_posted or ""
        self.category = category or []
        self.salary = salary or ""