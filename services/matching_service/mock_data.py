# matching_service/mock_data.py
def generate_mock_job_roles():
    """Generate mock job role data for the matching service"""
    
    roles = [
        {
            "title": "Communications Specialist",
            "description": "Responsible for internal and external communications, including content creation and media relations.",
            "department": "Marketing",
            "required_skills": [
                {"skill_id": 1, "importance": 0.9, "minimum_proficiency": 4},  # Speaking
                {"skill_id": 2, "importance": 0.8, "minimum_proficiency": 4},  # Persuasive Speaking
                {"skill_id": 3, "importance": 0.7, "minimum_proficiency": 3},  # Voice Modulation
                {"skill_id": 4, "importance": 0.9, "minimum_proficiency": 4},  # Information Documentation
                {"skill_id": 5, "importance": 0.6, "minimum_proficiency": 3},  # Active Listening
            ]
        },
        {
            "title": "Data Analyst",
            "description": "Analyzes data to identify trends and insights to support business decisions.",
            "department": "Analytics",
            "required_skills": [
                {"skill_id": 6, "importance": 0.9, "minimum_proficiency": 4},  # Numeracy
                {"skill_id": 7, "importance": 0.7, "minimum_proficiency": 3},  # Rule Application
                {"skill_id": 8, "importance": 0.6, "minimum_proficiency": 3},  # Scientific Method
                {"skill_id": 9, "importance": 0.9, "minimum_proficiency": 4},  # Data Validation
                {"skill_id": 5, "importance": 0.5, "minimum_proficiency": 3},  # Active Listening
            ]
        },
        {
            "title": "Project Manager",
            "description": "Coordinates team efforts to complete projects on time and within budget.",
            "department": "Operations",
            "required_skills": [
                {"skill_id": 1, "importance": 0.7, "minimum_proficiency": 3},  # Speaking
                {"skill_id": 4, "importance": 0.8, "minimum_proficiency": 4},  # Information Documentation
                {"skill_id": 5, "importance": 0.9, "minimum_proficiency": 4},  # Active Listening
                {"skill_id": 7, "importance": 0.6, "minimum_proficiency": 3},  # Rule Application
                {"skill_id": 13, "importance": 0.8, "minimum_proficiency": 4}, # Decision Making
            ]
        },
        {
            "title": "Logistics Coordinator",
            "description": "Manages the flow of goods and materials within the organization.",
            "department": "Operations",
            "required_skills": [
                {"skill_id": 6, "importance": 0.7, "minimum_proficiency": 3},  # Numeracy
                {"skill_id": 7, "importance": 0.8, "minimum_proficiency": 4},  # Rule Application
                {"skill_id": 13, "importance": 0.7, "minimum_proficiency": 3}, # Decision Making
                {"skill_id": 4, "importance": 0.6, "minimum_proficiency": 3},  # Information Documentation
                {"skill_id": 5, "importance": 0.5, "minimum_proficiency": 2},  # Active Listening
            ]
        },
    ]
    
    return roles