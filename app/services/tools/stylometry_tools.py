import re
from typing import List, Dict
import statistics

def compute_burstiness(text: str) -> float:
    """Computes sentence length variation. Higher = more human-like."""
    sentences = re.split(r'[.!?]+', text)
    lengths = [len(s.split()) for s in sentences if s.strip()]
    
    if len(lengths) <= 1:
        return 0.0
    
    mean_length = statistics.mean(lengths)
    if mean_length == 0:
        return 0.0
        
    stdev_length = statistics.stdev(lengths)
    return stdev_length / mean_length

def compute_type_token_ratio(text: str) -> float:
    """Computes lexical diversity (unique words / total words)."""
    words = re.findall(r'\w+', text.lower())
    if not words:
        return 0.0
    return len(set(words)) / len(words)

def compute_avg_sentence_length(text: str) -> float:
    sentences = re.split(r'[.!?]+', text)
    lengths = [len(s.split()) for s in sentences if s.strip()]
    if not lengths:
        return 0.0
    return statistics.mean(lengths)

def analyze_text_locally(text: str) -> Dict[str, float]:
    return {
        "burstiness": compute_burstiness(text),
        "type_token_ratio": compute_type_token_ratio(text),
        "avg_sentence_length": compute_avg_sentence_length(text)
    }

def extract_skills(text: str) -> List[str]:
    """Simple keyword extraction for common technical skills."""
    common_skills = [
        "python", "javascript", "typescript", "react", "node", "fastapi", 
        "docker", "kubernetes", "aws", "azure", "gcp", "sql", "mongodb",
        "postgresql", "redis", "pytorch", "tensorflow", "langchain",
        "java", "go", "rust", "cpp", "c#", "html", "css", "tailwind"
    ]
    found_skills = set()
    text_lower = text.lower()
    
    for skill in common_skills:
        # Match skill as a whole word
        if re.search(rf'\b{re.escape(skill)}\b', text_lower):
            found_skills.add(skill)
            
    return sorted(list(found_skills))
