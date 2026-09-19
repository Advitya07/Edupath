import re

SKILL_VOCABULARY = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "FastAPI", "SQL", "MongoDB",
    "Docker", "Kubernetes", "AWS", "Git", "Linux", "Machine Learning", "Pandas", "TensorFlow",
    "PyTorch", "CI/CD", "REST APIs", "Data Structures", "System Design",
]


def analyze_resume(text: str) -> dict:
    normalized = text.lower()
    skills = [skill for skill in SKILL_VOCABULARY if skill.lower() in normalized]
    years = re.search(r"(\d+)\+?\s+years?", normalized)
    experience = f"{years.group(1)} years" if years else "Early career"
    return {"skills": skills, "experience_level": experience, "text_length": len(text)}
