CURRENCY_BASE_USD = {
    "USD": 1.00,
    "EUR": 1.08,
    "GBP": 1.27,
    "INR": 0.012,
    "JPY": 0.0067,
    "KRW": 0.00075,
    "SGD": 0.74,
    "AUD": 0.66,
    "CAD": 0.74,
    "AED": 0.27,
    "SEK": 0.094,
    "CHF": 1.12,
}

BASE_SALARY_USD = {
    "intern":    {"min": 30000,  "max": 50000},
    "junior":    {"min": 55000,  "max": 85000},
    "mid":       {"min": 85000,  "max": 130000},
    "senior":    {"min": 130000, "max": 180000},
    "lead":      {"min": 170000, "max": 230000},
    "staff":     {"min": 210000, "max": 290000},
    "principal": {"min": 260000, "max": 380000},
    "manager":   {"min": 150000, "max": 210000},
    "director":  {"min": 220000, "max": 320000},
    "vp":        {"min": 280000, "max": 500000},
}

INDUSTRY_SALARY_MULTIPLIER = {
    "software": 1.00,
    "ai": 1.20,
    "cybersecurity": 1.10,
    "cloud": 1.05,
    "fintech": 1.15,
    "healthtech": 1.00,
    "edtech": 0.90,
    "ecommerce": 1.00,
    "automotive": 1.05,
    "manufacturing": 0.95,
    "banking": 1.10,
    "gaming": 1.00,
    "blockchain": 1.15,
    "robotics": 1.05,
    "aerospace": 1.05,
    "telecom": 1.00,
    "government": 0.85,
    "startup": 0.85,
    "unicorn": 1.20,
    "enterprise": 1.00,
}

COUNTRY_PURCHASING_POWER = {
    "US": 1.00, "GB": 0.95, "DE": 0.90, "FR": 0.85, "NL": 0.90, "SE": 0.85, "CH": 1.10,
    "CA": 0.90, "AU": 0.90, "SG": 0.95, "AE": 0.85, "JP": 0.85, "KR": 0.80, "IN": 0.40,
}

DEPARTMENT_SALARY_MULTIPLIER = {
    "engineering": 1.00,
    "data": 1.00,
    "product": 0.95,
    "design": 0.92,
    "marketing": 0.85,
    "sales": 0.90,
    "customer_success": 0.80,
    "people": 0.80,
    "finance": 0.90,
    "legal": 1.00,
    "operations": 0.85,
    "research": 1.05,
}

__all__ = ["CURRENCY_BASE_USD", "BASE_SALARY_USD", "INDUSTRY_SALARY_MULTIPLIER",
           "COUNTRY_PURCHASING_POWER", "DEPARTMENT_SALARY_MULTIPLIER"]
