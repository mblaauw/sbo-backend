
# user_service/mock_data.py
def generate_mock_users():
    """Generate mock user data for the user service"""
    
    users = [
        {
            "username": "johndoe",
            "email": "john.doe@example.com",
            "full_name": "John Doe",
            "department": "Engineering",
            "title": "Software Engineer",
            "bio": "Experienced software engineer with a passion for building scalable applications.",
            "skills": [
                {"skill_id": 1, "proficiency_level": 4, "is_verified": True, "source": "assessment"},
                {"skill_id": 5, "proficiency_level": 3, "is_verified": True, "source": "manager"},
                {"skill_id": 7, "proficiency_level": 5, "is_verified": True, "source": "assessment"},
                {"skill_id": 9, "proficiency_level": 3, "is_verified": False, "source": "self-assessment"}
            ]
        },
        {
            "username": "janesmith",
            "email": "jane.smith@example.com",
            "full_name": "Jane Smith",
            "department": "Marketing",
            "title": "Marketing Manager",
            "bio": "Creative marketing professional with expertise in digital campaigns.",
            "skills": [
                {"skill_id": 2, "proficiency_level": 5, "is_verified": True, "source": "assessment"},
                {"skill_id": 3, "proficiency_level": 4, "is_verified": True, "source": "peer"},
                {"skill_id": 5, "proficiency_level": 4, "is_verified": True, "source": "manager"},
                {"skill_id": 11, "proficiency_level": 3, "is_verified": False, "source": "self-assessment"}
            ]
        },
        {
            "username": "robertjohnson",
            "email": "robert.johnson@example.com",
            "full_name": "Robert Johnson",
            "department": "Operations",
            "title": "Project Manager",
            "bio": "Certified project manager with experience in agile methodologies.",
            "skills": [
                {"skill_id": 5, "proficiency_level": 5, "is_verified": True, "source": "assessment"},
                {"skill_id": 8, "proficiency_level": 4, "is_verified": True, "source": "manager"},
                {"skill_id": 13, "proficiency_level": 4, "is_verified": True, "source": "assessment"},
                {"skill_id": 2, "proficiency_level": 3, "is_verified": False, "source": "self-assessment"}
            ]
        }
    ]
    
    return users