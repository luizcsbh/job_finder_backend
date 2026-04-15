class Job:
    def __init__(self, title, company, location, description, url, source):
        self.title = title
        self.company = company
        self.location = location
        self.description = description
        self.url = url
        self.source = source
        self.score = 0
        self.ai_score = 0