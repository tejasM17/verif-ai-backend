BENEFITS = [
    {"slug": "health-insurance", "name": "Health Insurance", "category": "health", "weight": 0.18},
    {"slug": "dental-insurance", "name": "Dental Insurance", "category": "health", "weight": 0.10},
    {"slug": "vision-insurance", "name": "Vision Insurance", "category": "health", "weight": 0.08},
    {"slug": "mental-health", "name": "Mental Health Support", "category": "health", "weight": 0.09},
    {"slug": "life-insurance", "name": "Life Insurance", "category": "health", "weight": 0.05},
    {"slug": "401k", "name": "401(k) / Provident Fund", "category": "retirement", "weight": 0.12},
    {"slug": "equity", "name": "Equity / Stock Options", "category": "retirement", "weight": 0.10},
    {"slug": "pension", "name": "Pension Plan", "category": "retirement", "weight": 0.03},
    {"slug": "remote-work", "name": "Remote Work", "category": "flexibility", "weight": 0.15},
    {"slug": "flex-hours", "name": "Flexible Working Hours", "category": "flexibility", "weight": 0.12},
    {"slug": "unlimited-pto", "name": "Unlimited PTO", "category": "time_off", "weight": 0.08},
    {"slug": "paid-time-off", "name": "Generous Paid Time Off", "category": "time_off", "weight": 0.12},
    {"slug": "parental-leave", "name": "Parental Leave", "category": "time_off", "weight": 0.08},
    {"slug": "learning-budget", "name": "Learning & Development Budget", "category": "growth", "weight": 0.10},
    {"slug": "conference-budget", "name": "Conference & Talk Budget", "category": "growth", "weight": 0.06},
    {"slug": "certification", "name": "Certification Reimbursement", "category": "growth", "weight": 0.07},
    {"slug": "home-office", "name": "Home Office Stipend", "category": "equipment", "weight": 0.10},
    {"slug": "laptop", "name": "Top-tier Hardware Provided", "category": "equipment", "weight": 0.12},
    {"slug": "meals", "name": "Free Meals & Snacks", "category": "perks", "weight": 0.07},
    {"slug": "snacks", "name": "Pantry Stocked with Snacks", "category": "perks", "weight": 0.06},
    {"slug": "gym", "name": "Gym Membership / Wellness Stipend", "category": "wellness", "weight": 0.08},
    {"slug": "commuter", "name": "Commuter Benefits", "category": "perks", "weight": 0.06},
    {"slug": "relocation", "name": "Relocation Package", "category": "perks", "weight": 0.05},
    {"slug": "visa-sponsorship", "name": "Visa Sponsorship", "category": "perks", "weight": 0.07},
    {"slug": "childcare", "name": "Childcare Support", "category": "wellness", "weight": 0.04},
    {"slug": "transport", "name": "Transportation Allowance", "category": "perks", "weight": 0.05},
    {"slug": "phone-stipend", "name": "Phone & Internet Stipend", "category": "equipment", "weight": 0.06},
    {"slug": "team-events", "name": "Regular Team Events", "category": "culture", "weight": 0.08},
    {"slug": "hackathons", "name": "Internal Hackathons", "category": "culture", "weight": 0.04},
    {"slug": "dog-friendly", "name": "Dog-friendly Office", "category": "culture", "weight": 0.03},
    {"slug": "paid-volunteer", "name": "Paid Volunteer Time", "category": "culture", "weight": 0.04},
    {"slug": "match-donations", "name": "Charity Match Donations", "category": "culture", "weight": 0.03},
]

COMPANY_CULTURE_TEMPLATES = [
    "We are a {adjective} team that values {value1} and {value2}. Our culture is built on {foundation} and a relentless focus on {focus}.",
    "At {company}, we believe in {value1}, {value2}, and {value3}. We move fast, ship often, and learn continuously.",
    "We foster a {adjective} environment where {value1} is celebrated. Our team spans {geography} and works on {focus}.",
    "Our culture is defined by {value1}, {value2}, and {value3}. We hire exceptional people and trust them to do their best work.",
    "Join a {adjective} team that is reshaping {industry_phrase}. We invest heavily in {value1} and {value2}.",
]

CULTURE_VALUES = [
    "ownership", "transparency", "empathy", "craft", "curiosity", "bias for action",
    "customer obsession", "inclusion", "rigor", "humility", "speed", "quality",
    "innovation", "collaboration", "meritocracy", "long-term thinking",
]

ADJECTIVES = [
    "high-performance", "diverse", "global", "distributed", "tight-knit",
    "fast-moving", "engineering-driven", "research-driven", "product-led",
]

INDUSTRY_PHRASES = [
    "the future of finance", "next-generation infrastructure", "how the world builds software",
    "intelligent systems", "modern commerce", "the future of mobility",
    "trust on the internet", "how teams communicate", "the future of work",
    "human health", "modern healthcare", "the future of education",
]

__all__ = ["BENEFITS", "COMPANY_CULTURE_TEMPLATES", "CULTURE_VALUES", "ADJECTIVES", "INDUSTRY_PHRASES"]
