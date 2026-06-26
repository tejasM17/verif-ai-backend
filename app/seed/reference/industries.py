INDUSTRIES = [
    {
        "slug": "software",
        "name": "Software",
        "sub_industries": ["SaaS", "Developer Tools", "Productivity", "Enterprise Software", "Open Source"],
        "common_roles": ["Software Engineer", "Backend Engineer", "Frontend Engineer", "Full Stack Engineer", "Engineering Manager", "Staff Engineer", "Principal Engineer"],
        "tech_stack_categories": ["Programming", "Backend", "Frontend", "Cloud", "DevOps"],
        "headcount_distribution": {"1-10": 0.10, "11-50": 0.30, "51-200": 0.30, "201-500": 0.15, "501-1000": 0.08, "1001-5000": 0.05, "5001-10000": 0.01, "10000+": 0.01},
    },
    {
        "slug": "ai",
        "name": "Artificial Intelligence",
        "sub_industries": ["Machine Learning", "Deep Learning", "NLP", "Computer Vision", "Generative AI", "MLOps"],
        "common_roles": ["ML Engineer", "Research Scientist", "Applied AI Engineer", "Computer Vision Engineer", "NLP Engineer", "Data Scientist", "AI Product Manager"],
        "tech_stack_categories": ["AI/ML", "Data", "Cloud", "Programming", "Backend"],
        "headcount_distribution": {"1-10": 0.20, "11-50": 0.35, "51-200": 0.25, "201-500": 0.10, "501-1000": 0.05, "1001-5000": 0.03, "5001-10000": 0.01, "10000+": 0.01},
    },
    {
        "slug": "cybersecurity",
        "name": "Cybersecurity",
        "sub_industries": ["Network Security", "Endpoint Security", "Identity & Access", "Threat Intelligence", "Cloud Security", "Application Security"],
        "common_roles": ["Security Engineer", "Penetration Tester", "SOC Analyst", "Security Researcher", "CISO", "Application Security Engineer", "Incident Response Engineer"],
        "tech_stack_categories": ["Security", "Networking", "Cloud", "Backend", "DevOps"],
        "headcount_distribution": {"1-10": 0.10, "11-50": 0.30, "51-200": 0.30, "201-500": 0.15, "501-1000": 0.10, "1001-5000": 0.04, "5001-10000": 0.01, "10000+": 0.00},
    },
    {
        "slug": "cloud",
        "name": "Cloud Infrastructure",
        "sub_industries": ["Public Cloud", "Private Cloud", "Hybrid Cloud", "Edge Computing", "CDN"],
        "common_roles": ["Cloud Engineer", "Cloud Architect", "SRE", "DevOps Engineer", "Platform Engineer", "Kubernetes Engineer"],
        "tech_stack_categories": ["Cloud", "DevOps", "Networking", "Backend", "Security"],
        "headcount_distribution": {"1-10": 0.10, "11-50": 0.25, "51-200": 0.30, "201-500": 0.20, "501-1000": 0.10, "1001-5000": 0.04, "5001-10000": 0.01, "10000+": 0.00},
    },
    {
        "slug": "fintech",
        "name": "FinTech",
        "sub_industries": ["Payments", "Banking", "Lending", "Insurance", "Wealth Management", "Crypto", "RegTech"],
        "common_roles": ["Backend Engineer", "Risk Engineer", "Compliance Engineer", "Quant Developer", "Product Manager", "Data Engineer", "Mobile Engineer"],
        "tech_stack_categories": ["Backend", "Data", "Security", "Cloud", "Frontend"],
        "headcount_distribution": {"1-10": 0.08, "11-50": 0.25, "51-200": 0.25, "201-500": 0.20, "501-1000": 0.12, "1001-5000": 0.07, "5001-10000": 0.02, "10000+": 0.01},
    },
    {
        "slug": "healthtech",
        "name": "HealthTech",
        "sub_industries": ["Telemedicine", "Electronic Health Records", "Medical Imaging", "Genomics", "Wellness", "Health AI"],
        "common_roles": ["Software Engineer", "Clinical Data Scientist", "Health Informatics Specialist", "Mobile Engineer", "ML Engineer", "Product Manager"],
        "tech_stack_categories": ["Backend", "AI/ML", "Data", "Mobile", "Frontend"],
        "headcount_distribution": {"1-10": 0.15, "11-50": 0.35, "51-200": 0.25, "201-500": 0.15, "501-1000": 0.05, "1001-5000": 0.04, "5001-10000": 0.01, "10000+": 0.00},
    },
    {
        "slug": "edtech",
        "name": "EdTech",
        "sub_industries": ["K-12", "Higher Education", "Vocational Training", "Corporate Learning", "Language Learning", "Test Prep"],
        "common_roles": ["Full Stack Engineer", "Curriculum Engineer", "Mobile Engineer", "Learning Designer", "Product Manager", "Data Analyst"],
        "tech_stack_categories": ["Frontend", "Mobile", "Backend", "AI/ML", "Data"],
        "headcount_distribution": {"1-10": 0.20, "11-50": 0.40, "51-200": 0.20, "201-500": 0.10, "501-1000": 0.05, "1001-5000": 0.04, "5001-10000": 0.01, "10000+": 0.00},
    },
    {
        "slug": "ecommerce",
        "name": "E-Commerce",
        "sub_industries": ["Marketplace", "D2C", "Quick Commerce", "B2B Commerce", "Social Commerce"],
        "common_roles": ["Full Stack Engineer", "Mobile Engineer", "Data Engineer", "Growth Engineer", "Product Manager", "Category Manager"],
        "tech_stack_categories": ["Frontend", "Backend", "Mobile", "Data", "Cloud"],
        "headcount_distribution": {"1-10": 0.10, "11-50": 0.30, "51-200": 0.25, "201-500": 0.20, "501-1000": 0.08, "1001-5000": 0.05, "5001-10000": 0.01, "10000+": 0.01},
    },
    {
        "slug": "automotive",
        "name": "Automotive",
        "sub_industries": ["EV", "Autonomous Driving", "Connected Cars", "OEM", "Aftermarket"],
        "common_roles": ["Embedded Software Engineer", "C++ Engineer", "Computer Vision Engineer", "Mechanical Engineer", "Systems Engineer", "Robotics Engineer"],
        "tech_stack_categories": ["Embedded", "AI/ML", "Backend", "Mobile", "Hardware"],
        "headcount_distribution": {"1-10": 0.05, "11-50": 0.15, "51-200": 0.20, "201-500": 0.20, "501-1000": 0.15, "1001-5000": 0.15, "5001-10000": 0.05, "10000+": 0.05},
    },
    {
        "slug": "manufacturing",
        "name": "Manufacturing",
        "sub_industries": ["Industrial Automation", "IoT", "3D Printing", "Robotics", "Semiconductor"],
        "common_roles": ["Embedded Engineer", "IoT Engineer", "Controls Engineer", "Robotics Engineer", "Quality Engineer", "Operations Manager"],
        "tech_stack_categories": ["Embedded", "IoT", "Hardware", "Data", "Backend"],
        "headcount_distribution": {"1-10": 0.05, "11-50": 0.15, "51-200": 0.20, "201-500": 0.20, "501-1000": 0.15, "1001-5000": 0.15, "5001-10000": 0.05, "10000+": 0.05},
    },
    {
        "slug": "banking",
        "name": "Banking",
        "sub_industries": ["Retail Banking", "Investment Banking", "Corporate Banking", "Private Banking", "Digital Banking"],
        "common_roles": ["Backend Engineer", "Risk Analyst", "Quant Developer", "Compliance Officer", "Mobile Engineer", "Product Manager"],
        "tech_stack_categories": ["Backend", "Data", "Security", "Mobile", "Frontend"],
        "headcount_distribution": {"1-10": 0.02, "11-50": 0.10, "51-200": 0.15, "201-500": 0.20, "501-1000": 0.15, "1001-5000": 0.20, "5001-10000": 0.10, "10000+": 0.08},
    },
    {
        "slug": "gaming",
        "name": "Gaming",
        "sub_industries": ["Mobile Games", "Console Games", "PC Games", "Cloud Gaming", "Esports"],
        "common_roles": ["Game Developer", "Unity Engineer", "Unreal Engineer", "Game Designer", "3D Artist", "Game Producer"],
        "tech_stack_categories": ["Game Dev", "Graphics", "Mobile", "Backend", "AI/ML"],
        "headcount_distribution": {"1-10": 0.15, "11-50": 0.35, "51-200": 0.25, "201-500": 0.15, "501-1000": 0.05, "1001-5000": 0.04, "5001-10000": 0.01, "10000+": 0.00},
    },
    {
        "slug": "blockchain",
        "name": "Blockchain",
        "sub_industries": ["Layer 1", "Layer 2", "DeFi", "NFT", "DAOs", "Web3"],
        "common_roles": ["Smart Contract Engineer", "Solidity Developer", "Protocol Engineer", "Cryptography Engineer", "Web3 Frontend Engineer", "Rust Engineer"],
        "tech_stack_categories": ["Blockchain", "Backend", "Cryptography", "Frontend", "DevOps"],
        "headcount_distribution": {"1-10": 0.30, "11-50": 0.45, "51-200": 0.15, "201-500": 0.05, "501-1000": 0.03, "1001-5000": 0.01, "5001-10000": 0.01, "10000+": 0.00},
    },
    {
        "slug": "robotics",
        "name": "Robotics",
        "sub_industries": ["Industrial Robots", "Service Robots", "Drones", "Autonomous Systems", "Medical Robotics"],
        "common_roles": ["Robotics Engineer", "ROS Developer", "Controls Engineer", "Computer Vision Engineer", "Mechanical Engineer", "SLAM Engineer"],
        "tech_stack_categories": ["Robotics", "Embedded", "AI/ML", "Hardware", "Computer Vision"],
        "headcount_distribution": {"1-10": 0.15, "11-50": 0.35, "51-200": 0.25, "201-500": 0.15, "501-1000": 0.05, "1001-5000": 0.04, "5001-10000": 0.01, "10000+": 0.00},
    },
    {
        "slug": "aerospace",
        "name": "Aerospace",
        "sub_industries": ["Commercial Aviation", "Defense", "Space", "Satellites", "Drones"],
        "common_roles": ["Aerospace Engineer", "Systems Engineer", "Embedded Engineer", "GNSS Engineer", "Propulsion Engineer", "Avionics Engineer"],
        "tech_stack_categories": ["Embedded", "Hardware", "Systems", "Aerospace", "Security"],
        "headcount_distribution": {"1-10": 0.05, "11-50": 0.10, "51-200": 0.20, "201-500": 0.20, "501-1000": 0.15, "1001-5000": 0.20, "5001-10000": 0.05, "10000+": 0.05},
    },
    {
        "slug": "telecom",
        "name": "Telecommunications",
        "sub_industries": ["Wireless", "Fiber Optics", "5G", "Satellite Comms", "IoT Networks"],
        "common_roles": ["Network Engineer", "RF Engineer", "Telecom Engineer", "Backend Engineer", "Data Engineer"],
        "tech_stack_categories": ["Networking", "Backend", "Cloud", "Embedded", "Data"],
        "headcount_distribution": {"1-10": 0.02, "11-50": 0.08, "51-200": 0.15, "201-500": 0.20, "501-1000": 0.15, "1001-5000": 0.20, "5001-10000": 0.10, "10000+": 0.10},
    },
    {
        "slug": "government",
        "name": "Government",
        "sub_industries": ["Federal", "State", "Defense", "Public Services", "Civic Tech"],
        "common_roles": ["Software Engineer", "Data Engineer", "Security Engineer", "Systems Administrator", "Policy Analyst"],
        "tech_stack_categories": ["Backend", "Security", "Data", "Cloud", "Frontend"],
        "headcount_distribution": {"1-10": 0.05, "11-50": 0.10, "51-200": 0.15, "201-500": 0.20, "501-1000": 0.15, "1001-5000": 0.20, "5001-10000": 0.10, "10000+": 0.05},
    },
    {
        "slug": "startup",
        "name": "Startup",
        "sub_industries": ["Pre-seed", "Seed Stage", "Series A", "Series B", "Bootstrapped"],
        "common_roles": ["Founding Engineer", "Full Stack Engineer", "Product Manager", "Designer", "Growth Marketer"],
        "tech_stack_categories": ["Frontend", "Backend", "Mobile", "DevOps", "AI/ML"],
        "headcount_distribution": {"1-10": 0.50, "11-50": 0.40, "51-200": 0.08, "201-500": 0.01, "501-1000": 0.01, "1001-5000": 0.00, "5001-10000": 0.00, "10000+": 0.00},
    },
    {
        "slug": "unicorn",
        "name": "Unicorn",
        "sub_industries": ["FinTech Unicorn", "AI Unicorn", "SaaS Unicorn", "Mobility Unicorn", "HealthTech Unicorn"],
        "common_roles": ["Staff Engineer", "Engineering Manager", "Product Manager", "Designer", "Data Scientist"],
        "tech_stack_categories": ["Backend", "Frontend", "Data", "Cloud", "AI/ML"],
        "headcount_distribution": {"1-10": 0.00, "11-50": 0.05, "51-200": 0.20, "201-500": 0.30, "501-1000": 0.25, "1001-5000": 0.15, "5001-10000": 0.04, "10000+": 0.01},
    },
    {
        "slug": "enterprise",
        "name": "Enterprise",
        "sub_industries": ["Fortune 500", "Global 2000", "Multinational", "Conglomerate"],
        "common_roles": ["Senior Engineer", "Architect", "Project Manager", "Business Analyst", "Solutions Engineer"],
        "tech_stack_categories": ["Backend", "Cloud", "Security", "Data", "Frontend"],
        "headcount_distribution": {"1-10": 0.00, "11-50": 0.02, "51-200": 0.08, "201-500": 0.15, "501-1000": 0.15, "1001-5000": 0.30, "5001-10000": 0.20, "10000+": 0.10},
    },
]

INDUSTRY_BY_SLUG = {ind["slug"]: ind for ind in INDUSTRIES}

COUNTRY_WEIGHTS = {
    "US": 25, "IN": 20, "GB": 8, "DE": 7, "CA": 5, "SG": 4, "AU": 4,
    "JP": 4, "KR": 3, "AE": 3, "NL": 3, "FR": 3, "SE": 2, "CH": 3,
}

INDUSTRY_WEIGHTS = {
    "software": 12, "ai": 9, "cybersecurity": 6, "cloud": 5, "fintech": 8,
    "healthtech": 5, "edtech": 4, "ecommerce": 8, "automotive": 4, "manufacturing": 5,
    "banking": 5, "gaming": 4, "blockchain": 3, "robotics": 3, "aerospace": 3,
    "telecom": 3, "government": 2, "startup": 4, "unicorn": 4, "enterprise": 2,
}

HIRING_STATUS_WEIGHTS = {"actively_hiring": 0.6, "limited": 0.3, "closed": 0.1}
VERIFICATION_STATUS_WEIGHTS = {"verified": 0.7, "pending": 0.2, "unverified": 0.1}
COMPANY_SIZE_BUCKETS = ["1-10", "11-50", "51-200", "201-500", "501-1000", "1001-5000", "5001-10000", "10000+"]

__all__ = [
    "INDUSTRIES", "INDUSTRY_BY_SLUG", "COUNTRY_WEIGHTS", "INDUSTRY_WEIGHTS",
    "HIRING_STATUS_WEIGHTS", "VERIFICATION_STATUS_WEIGHTS", "COMPANY_SIZE_BUCKETS",
]
