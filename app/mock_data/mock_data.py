"""
Simplified mock data generation for SBO services.
Data is loaded from JSON files and processed for database use.
"""

import json
import os
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger("sbo.mock_data")

# Define path to mock data files
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_data")

def load_json_data(filename: str) -> Dict[str, Any]:
    """Load data from a JSON file in the mock_data directory"""
    try:
        file_path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(file_path):
            logger.warning(f"Mock data file not found: {file_path}")
            return {}
            
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading mock data from {filename}: {str(e)}")
        return {}

def get_mock_skills_taxonomy() -> Dict[str, List[Dict[str, Any]]]:
    """Get mock skills taxonomy data"""
    return load_json_data("skills_taxonomy.json")

def get_mock_users() -> List[Dict[str, Any]]:
    """Get mock user data"""
    return load_json_data("users.json")

def get_mock_job_roles() -> List[Dict[str, Any]]:
    """Get mock job role data"""
    return load_json_data("job_roles.json")

def get_mock_assessments() -> List[Dict[str, Any]]:
    """Get mock assessment data"""
    return load_json_data("assessments.json")

def generate_assessment_results(user_count: int = 5, assessment_count: int = 4) -> List[Dict[str, Any]]:
    """Generate mock assessment results for users"""
    results = []
    
    for user_id in range(1, user_count + 1):
        # Each user has taken some assessments
        taken_assessments = random.sample(
            range(1, assessment_count + 1), 
            random.randint(1, assessment_count)
        )
        
        for assessment_id in taken_assessments:
            # Generate random score between 40 and 100
            score = random.randint(40, 100)
            
            # Determine proficiency level based on score
            if score >= 90:
                proficiency_level = 5
            elif score >= 80:
                proficiency_level = 4
            elif score >= 70:
                proficiency_level = 3
            elif score >= 60:
                proficiency_level = 2
            else:
                proficiency_level = 1
                
            # Generate random completion date within the last 30 days
            days_ago = random.randint(0, 30)
            completed_at = datetime.now() - timedelta(days=days_ago)
            
            results.append({
                "user_id": user_id,
                "assessment_id": assessment_id,
                "score": score,
                "proficiency_level": proficiency_level,
                "completed_at": completed_at
            })
    
    return results

def generate_llm_assessment_questions(skill_name: str, num_questions: int = 3) -> Dict[str, Any]:
    """Generate mock assessment questions as if from an LLM"""
    # Load question templates from JSON
    question_templates = load_json_data("question_templates.json")
    
    # Get questions for the requested skill or provide generic ones
    if skill_name in question_templates:
        questions = question_templates[skill_name]
    else:
        # Generic questions for any skill
        questions = question_templates.get("generic", [])
        
        # Customize for the specific skill
        for q in questions:
            q["question"] = q["question"].replace("{skill_name}", skill_name)
            q["explanation"] = q["explanation"].replace("{skill_name}", skill_name)
    
    # Return the requested number of questions
    result = {
        "skill_name": skill_name,
        "questions": questions[:num_questions]
    }
    return result

def analyze_resume(resume_text: str) -> Dict[str, Any]:
    """Mock function to analyze a resume and extract skills and experiences"""
    # Load skill dictionary for matching
    skills_data = load_json_data("resume_skills.json")
    potential_skills = skills_data.get("skills", [])
    
    # Extract skills based on keywords in the resume
    skills = []
    for skill in potential_skills:
        if skill.lower() in resume_text.lower() or random.random() < 0.15:
            confidence = round(random.uniform(0.6, 0.95), 2)
            # Find context by locating a substring around the skill mention
            if skill.lower() in resume_text.lower():
                start_idx = max(0, resume_text.lower().find(skill.lower()) - 30)
                end_idx = min(len(resume_text), resume_text.lower().find(skill.lower()) + len(skill) + 30)
                context = resume_text[start_idx:end_idx]
            else:
                context = ""
                
            skills.append({
                "name": skill,
                "confidence": confidence,
                "evidence": context
            })
    
    # Generate mock experiences
    experiences = []
    job_titles = skills_data.get("job_titles", [])
    
    for title in job_titles:
        if title.lower() in resume_text.lower() or random.random() < 0.1:
            # Create a mock experience entry
            experience = {
                "title": title,
                "company": f"Company {random.choice(['A', 'B', 'C', 'D', 'E'])}",
                "duration": f"{random.randint(1, 5)} years",
                "description": f"Worked as a {title} performing various responsibilities and projects.",
                "skills": random.sample([s["name"] for s in skills], min(3, len(skills)))
            }
            experiences.append(experience)
    
    # Mock education
    education = [
        {
            "degree": random.choice(["Bachelor's", "Master's", "PhD"]),
            "field": random.choice(["Computer Science", "Business", "Engineering", "Marketing"]),
            "institution": random.choice(["State University", "Tech Institute", "Business School", "College of Arts"]),
            "year": random.randint(2000, 2022)
        }
    ]
    
    # Generate suggested roles based on extracted skills
    suggested_roles = []
    skill_to_role_map = skills_data.get("skill_to_role_map", {})
    
    # Add suggested roles based on skills
    for skill in skills:
        if skill["name"] in skill_to_role_map and random.random() < 0.7:
            suggested_roles.extend(skill_to_role_map[skill["name"]])
    
    # Remove duplicates and limit to 5 roles
    suggested_roles = list(set(suggested_roles))[:5]
    
    return {
        "skills": skills,
        "experiences": experiences,
        "education": education,
        "summary": f"Professional with skills in {', '.join([s['name'] for s in skills[:3]])}.",
        "suggested_roles": suggested_roles
    }

def generate_learning_path(
    user_id: int, 
    target_skills: List[Dict[str, Any]], 
    current_skills: List[Dict[str, Any]], 
    time_frame: Optional[str] = None
) -> Dict[str, Any]:
    """Generate a mock personalized learning path"""
    # Create a set of current skill names for easy lookup
    current_skill_names = {skill["name"].lower() for skill in current_skills}
    
    # Filter target skills to those not already possessed
    new_target_skills = [
        skill for skill in target_skills 
        if skill["name"].lower() not in current_skill_names
    ]
    
    # Load learning resources templates
    learning_resources = load_json_data("learning_resources.json")
    
    steps = []
    
    # Create steps for each new skill to learn
    for skill in new_target_skills:
        skill_name = skill["name"]
        
        # Get resources for this type of skill if available
        skill_category = skill.get("category", "general")
        resources_pool = learning_resources.get(skill_category, learning_resources.get("general", []))
        
        # Select 2-3 resources randomly
        num_resources = random.randint(2, 3)
        resources = random.sample(resources_pool, min(num_resources, len(resources_pool)))
        
        # Customize resources for this skill
        for resource in resources:
            resource = resource.copy()  # Create a copy to avoid modifying the original
            resource["name"] = resource["name"].replace("{skill}", skill_name)
            if "description" in resource:
                resource["description"] = resource["description"].replace("{skill}", skill_name)
        
        # Create learning step
        steps.append({
            "name": f"Learn {skill_name}",
            "description": f"Develop proficiency in {skill_name} through structured learning and practice",
            "duration": f"{random.randint(2, 8)} weeks",
            "resources": resources,
            "skills_addressed": [skill_name]
        })
    
    # If all target skills are already possessed, suggest advanced learning
    if not new_target_skills:
        advanced_resources = learning_resources.get("advanced", [])
        
        steps = [{
            "name": "Advanced Skill Enhancement",
            "description": "Deepen your existing skills through practical application",
            "duration": "4 weeks",
            "resources": advanced_resources,
            "skills_addressed": [skill["name"] for skill in current_skills[:3]]
        }]
    
    # Calculate total duration
    total_weeks = sum([int(step["duration"].split()[0]) for step in steps])
    
    return {
        "user_id": user_id,
        "title": "Personalized Skill Development Plan",
        "description": f"A customized learning path to help you acquire {len(new_target_skills)} new skills",
        "total_duration": f"{total_weeks} weeks",
        "steps": steps
    }