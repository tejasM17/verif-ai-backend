SENIORITY_LEVELS = [
    {"slug": "intern", "name": "Intern", "weight": 0.03, "min_experience": 0, "max_experience": 0, "salary_multiplier": 0.30},
    {"slug": "junior", "name": "Junior", "weight": 0.10, "min_experience": 0, "max_experience": 2, "salary_multiplier": 0.55},
    {"slug": "mid", "name": "Mid-Level", "weight": 0.30, "min_experience": 2, "max_experience": 5, "salary_multiplier": 0.85},
    {"slug": "senior", "name": "Senior", "weight": 0.30, "min_experience": 5, "max_experience": 8, "salary_multiplier": 1.20},
    {"slug": "lead", "name": "Lead", "weight": 0.12, "min_experience": 7, "max_experience": 12, "salary_multiplier": 1.55},
    {"slug": "staff", "name": "Staff", "weight": 0.08, "min_experience": 8, "max_experience": 15, "salary_multiplier": 1.85},
    {"slug": "principal", "name": "Principal", "weight": 0.05, "min_experience": 10, "max_experience": 18, "salary_multiplier": 2.20},
    {"slug": "manager", "name": "Manager", "weight": 0.07, "min_experience": 7, "max_experience": 15, "salary_multiplier": 1.60},
    {"slug": "director", "name": "Director", "weight": 0.03, "min_experience": 12, "max_experience": 20, "salary_multiplier": 2.50},
    {"slug": "vp", "name": "VP", "weight": 0.02, "min_experience": 15, "max_experience": 25, "salary_multiplier": 3.20},
]

DEPARTMENTS = [
    {"slug": "engineering", "name": "Engineering", "weight": 0.40},
    {"slug": "product", "name": "Product", "weight": 0.10},
    {"slug": "design", "name": "Design", "weight": 0.06},
    {"slug": "data", "name": "Data", "weight": 0.08},
    {"slug": "marketing", "name": "Marketing", "weight": 0.06},
    {"slug": "sales", "name": "Sales", "weight": 0.10},
    {"slug": "customer_success", "name": "Customer Success", "weight": 0.05},
    {"slug": "people", "name": "People & HR", "weight": 0.04},
    {"slug": "finance", "name": "Finance", "weight": 0.03},
    {"slug": "legal", "name": "Legal", "weight": 0.02},
    {"slug": "operations", "name": "Operations", "weight": 0.04},
    {"slug": "research", "name": "Research", "weight": 0.02},
]

EMPLOYMENT_TYPES = [
    {"slug": "full_time", "name": "Full-time", "weight": 0.75},
    {"slug": "part_time", "name": "Part-time", "weight": 0.05},
    {"slug": "contract", "name": "Contract", "weight": 0.10},
    {"slug": "internship", "name": "Internship", "weight": 0.05},
    {"slug": "freelance", "name": "Freelance", "weight": 0.05},
]

EXPERIENCE_LEVELS = [
    {"slug": "entry", "name": "Entry Level", "weight": 0.10, "min_years": 0, "max_years": 1},
    {"slug": "junior", "name": "Junior", "weight": 0.20, "min_years": 1, "max_years": 3},
    {"slug": "mid", "name": "Mid Level", "weight": 0.30, "min_years": 3, "max_years": 6},
    {"slug": "senior", "name": "Senior", "weight": 0.25, "min_years": 6, "max_years": 10},
    {"slug": "lead", "name": "Lead", "weight": 0.08, "min_years": 8, "max_years": 15},
    {"slug": "principal", "name": "Principal", "weight": 0.04, "min_years": 10, "max_years": 20},
    {"slug": "executive", "name": "Executive", "weight": 0.03, "min_years": 15, "max_years": 30},
]

WORK_MODES = [
    {"slug": "remote", "name": "Remote", "weight": 0.40},
    {"slug": "hybrid", "name": "Hybrid", "weight": 0.40},
    {"slug": "onsite", "name": "On-site", "weight": 0.20},
]

EDUCATION_LEVELS = [
    {"slug": "high_school", "name": "High School", "weight": 0.05},
    {"slug": "associate", "name": "Associate Degree", "weight": 0.05},
    {"slug": "bachelor", "name": "Bachelor's Degree", "weight": 0.55},
    {"slug": "master", "name": "Master's Degree", "weight": 0.25},
    {"slug": "phd", "name": "PhD", "weight": 0.05},
    {"slug": "any", "name": "Any", "weight": 0.05},
]

JOB_CATEGORIES = [
    {"slug": "software-engineering", "name": "Software Engineering", "description": "Build and maintain software systems and applications."},
    {"slug": "data-science", "name": "Data Science & Analytics", "description": "Extract insights and build predictive models from data."},
    {"slug": "machine-learning", "name": "Machine Learning & AI", "description": "Design, train and deploy ML and AI systems."},
    {"slug": "devops", "name": "DevOps & Site Reliability", "description": "Operate and automate production infrastructure."},
    {"slug": "frontend", "name": "Frontend Engineering", "description": "Build user interfaces and web experiences."},
    {"slug": "backend", "name": "Backend Engineering", "description": "Design server-side systems and APIs."},
    {"slug": "mobile", "name": "Mobile Engineering", "description": "Build iOS and Android applications."},
    {"slug": "product-management", "name": "Product Management", "description": "Define product strategy and roadmap."},
    {"slug": "product-design", "name": "Product Design", "description": "Design user experiences and interfaces."},
    {"slug": "data-engineering", "name": "Data Engineering", "description": "Build data pipelines and warehousing."},
    {"slug": "security", "name": "Information Security", "description": "Protect systems and data from threats."},
    {"slug": "qa", "name": "Quality Assurance", "description": "Test and verify product quality."},
    {"slug": "marketing", "name": "Marketing", "description": "Grow brand awareness and demand."},
    {"slug": "sales", "name": "Sales", "description": "Close deals and grow revenue."},
    {"slug": "customer-support", "name": "Customer Support", "description": "Help customers succeed with the product."},
    {"slug": "people", "name": "People & HR", "description": "Talent acquisition and people operations."},
    {"slug": "finance", "name": "Finance & Accounting", "description": "Manage financial planning and reporting."},
    {"slug": "legal", "name": "Legal", "description": "Handle legal matters and compliance."},
    {"slug": "operations", "name": "Operations", "description": "Run day-to-day business operations."},
    {"slug": "research", "name": "Research", "description": "Advance the state of the art."},
    {"slug": "blockchain", "name": "Blockchain & Web3", "description": "Build decentralized systems and applications."},
    {"slug": "gaming", "name": "Game Development", "description": "Design and develop interactive games."},
    {"slug": "robotics", "name": "Robotics", "description": "Design and program robotic systems."},
    {"slug": "embedded", "name": "Embedded Systems", "description": "Develop firmware and embedded software."},
    {"slug": "aerospace", "name": "Aerospace Engineering", "description": "Design aircraft, spacecraft and related systems."},
    {"slug": "automotive", "name": "Automotive Engineering", "description": "Engineer vehicles and mobility systems."},
    {"slug": "healthcare", "name": "Healthcare & Clinical", "description": "Deliver healthcare services and outcomes."},
    {"slug": "education", "name": "Education & Training", "description": "Teach and develop educational content."},
    {"slug": "manufacturing", "name": "Manufacturing & Production", "description": "Run production and supply chains."},
    {"slug": "executive", "name": "Executive & Leadership", "description": "Lead organizations and teams."},
]

JOB_STATUSES = [
    {"slug": "draft", "name": "Draft", "weight": 0.05},
    {"slug": "open", "name": "Open", "weight": 0.60},
    {"slug": "paused", "name": "Paused", "weight": 0.10},
    {"slug": "closed", "name": "Closed", "weight": 0.15},
    {"slug": "filled", "name": "Filled", "weight": 0.10},
]

RECRUITER_DESIGNATIONS = [
    "Talent Acquisition Lead",
    "Senior Technical Recruiter",
    "Technical Recruiter",
    "HR Manager",
    "Head of Talent",
    "Talent Partner",
    "Recruiting Coordinator",
    "University Recruiter",
    "Engineering Recruiter",
    "Sourcing Specialist",
    "Talent Acquisition Manager",
    "People Operations Specialist",
    "Hiring Manager",
    "Senior Talent Partner",
    "Director of Talent",
    "VP of People",
    "Campus Recruiter",
    "Diversity & Inclusion Recruiter",
    "Executive Recruiter",
    "Contract Recruiter",
]

RECRUITER_SPECIALTIES = [
    "Engineering", "Product Management", "Design", "Data Science", "ML & AI",
    "DevOps & SRE", "Mobile", "Frontend", "Backend", "Full Stack",
    "Security", "Blockchain", "Cloud", "Embedded", "Robotics",
    "Sales", "Marketing", "Customer Success", "Operations", "Finance",
    "Legal", "People & HR", "Executive Search", "University Hiring",
    "Diversity Hiring", "International Hiring",
]

__all__ = [
    "SENIORITY_LEVELS", "DEPARTMENTS", "EMPLOYMENT_TYPES", "EXPERIENCE_LEVELS",
    "WORK_MODES", "EDUCATION_LEVELS", "JOB_CATEGORIES", "JOB_STATUSES",
    "RECRUITER_DESIGNATIONS", "RECRUITER_SPECIALTIES",
]
