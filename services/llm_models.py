# services/llm_models.py
"""
Implementation of LLM-based functions for the SBO application.
These functions simulate the behavior of language models for skill extraction,
assessment generation, and other NLP tasks in the system.
"""

import logging
import random
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Import from mock_data to reuse mock data generation functions
from services.mock_data import (
    generate_mock_llm_assessment_questions,
    mock_analyze_resume,
    generate_mock_learning_path
)

logger = logging.getLogger(__name__)

def extract_skills_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extract skills from unstructured text using NLP techniques.
    
    Args:
        text: Unstructured text from which to extract skills
        
    Returns:
        List of extracted skills with confidence scores
    """
    logger.info(f"Extracting skills from text of length {len(text)}")
    
    # List of common technical and soft skills to look for
    common_skills = [
        {"name": "Python", "keywords": ["python", "django", "flask", "pandas", "numpy"]},
        {"name": "JavaScript", "keywords": ["javascript", "js", "node", "react", "angular", "vue"]},
        {"name": "SQL", "keywords": ["sql", "database", "postgresql", "mysql", "oracle"]},
        {"name": "Data Analysis", "keywords": ["data analysis", "analytics", "statistics", "data science"]},
        {"name": "Machine Learning", "keywords": ["machine learning", "ml", "ai", "artificial intelligence"]},
        {"name": "Communication", "keywords": ["communication", "presenting", "writing", "verbal"]},
        {"name": "Leadership", "keywords": ["leadership", "team lead", "manager", "director"]},
        {"name": "Project Management", "keywords": ["project management", "agile", "scrum", "kanban"]},
        {"name": "Problem Solving", "keywords": ["problem solving", "analytical", "troubleshooting"]},
        {"name": "Teamwork", "keywords": ["teamwork", "collaboration", "cooperative"]}
    ]
    
    # Basic skill extraction based on keyword matching
    extracted_skills = []
    text_lower = text.lower()
    
    for skill in common_skills:
        # Check for each keyword
        for keyword in skill["keywords"]:
            if keyword in text_lower:
                # Extract context around the keyword
                match_pos = text_lower.find(keyword)
                start_pos = max(0, match_pos - 30)
                end_pos = min(len(text), match_pos + len(keyword) + 30)
                context = text[start_pos:end_pos]
                
                # Calculate a confidence score based on keyword position and frequency
                confidence = min(0.95, 0.7 + 0.05 * text_lower.count(keyword))
                
                extracted_skills.append({
                    "skill_name": skill["name"],
                    "confidence": round(confidence, 2),
                    "context": context
                })
                # Once we find one keyword for this skill, move to next skill
                break
    
    # If no skills were found, add a few with low confidence based on the text length
    if not extracted_skills and len(text) > 50:
        num_random_skills = min(3, len(common_skills))
        random_skills = random.sample(common_skills, num_random_skills)
        
        for skill in random_skills:
            extracted_skills.append({
                "skill_name": skill["name"],
                "confidence": round(random.uniform(0.5, 0.65), 2),
                "context": "Inferred from general content"
            })
    
    # Sort by confidence (highest first)
    extracted_skills.sort(key=lambda x: x["confidence"], reverse=True)
    
    return extracted_skills

def map_skills_to_taxonomy(skills: List[str], taxonomy: List[str]) -> List[Dict[str, Any]]:
    """
    Map free-text skills to a standardized skills taxonomy.
    
    Args:
        skills: List of skill names to map
        taxonomy: List of standardized skill names in the taxonomy
        
    Returns:
        List of mapped skills with confidence scores
    """
    logger.info(f"Mapping {len(skills)} skills to taxonomy with {len(taxonomy)} items")
    
    mapped_skills = []
    
    for skill in skills:
        skill_lower = skill.lower()
        
        # Try exact match first
        exact_match = None
        for idx, tax_skill in enumerate(taxonomy):
            if tax_skill.lower() == skill_lower:
                exact_match = {
                    "original_text": skill,
                    "skill_id": idx + 1,  # 1-based index for skill IDs
                    "skill_name": tax_skill,
                    "confidence": 1.0
                }
                break
        
        if exact_match:
            mapped_skills.append(exact_match)
            continue
            
        # Try fuzzy matching
        best_match = None
        best_score = 0
        
        for idx, tax_skill in enumerate(taxonomy):
            # Simple fuzzy match: check if one is substring of the other
            if skill_lower in tax_skill.lower() or tax_skill.lower() in skill_lower:
                # Calculate similarity score based on string lengths
                score = len(set(skill_lower).intersection(set(tax_skill.lower()))) / max(len(skill_lower), len(tax_skill.lower()))
                if score > best_score:
                    best_score = score
                    best_match = {
                        "original_text": skill,
                        "skill_id": idx + 1,  # 1-based index for skill IDs
                        "skill_name": tax_skill,
                        "confidence": round(0.5 + 0.5 * best_score, 2)
                    }
        
        if best_match and best_score > 0.3:  # Only add if we have a reasonable match
            mapped_skills.append(best_match)
        else:
            # No good match found, find the closest skill alphabetically
            taxonomy_lower = [t.lower() for t in taxonomy]
            closest_idx = min(range(len(taxonomy_lower)), 
                           key=lambda i: sum(1 for a, b in zip(skill_lower, taxonomy_lower[i]) if a != b))
            
            mapped_skills.append({
                "original_text": skill,
                "skill_id": closest_idx + 1,
                "skill_name": taxonomy[closest_idx],
                "confidence": 0.5  # Low confidence since it's just alphabetically similar
            })
            
    return mapped_skills

def generate_assessment_questions(skill_name: str, skill_description: Optional[str] = None, 
                                 num_questions: int = 5, difficulty: str = "medium") -> List[Dict[str, Any]]:
    """
    Generate assessment questions for a specific skill.
    
    Args:
        skill_name: Name of the skill to generate questions for
        skill_description: Optional description of the skill
        num_questions: Number of questions to generate
        difficulty: Difficulty level ("easy", "medium", "hard")
        
    Returns:
        List of questions with options, correct answers, and explanations
    """
    logger.info(f"Generating {num_questions} {difficulty} questions for skill: {skill_name}")
    
    # Use the existing mock function
    result = generate_mock_llm_assessment_questions(skill_name, num_questions)
    
    # Add difficulty adjustment if needed
    if difficulty == "easy":
        # For easy questions, make the correct answer more obvious
        for q in result["questions"]:
            q["explanation"] += " This is a fundamental concept in this skill area."
    elif difficulty == "hard":
        # For hard questions, make them more challenging
        for q in result["questions"]:
            q["explanation"] = "This is an advanced concept. " + q["explanation"]
    
    return result["questions"]

def analyze_resume(resume_text: str) -> Dict[str, Any]:
    """
    Analyze a resume to extract skills, experience, and other relevant information.
    
    Args:
        resume_text: Text content of the resume
        
    Returns:
        Dictionary with extracted information
    """
    logger.info(f"Analyzing resume of length {len(resume_text)}")
    
    # Use the existing mock function
    return mock_analyze_resume(resume_text)

def generate_learning_path(user_id: int, target_skills: List[Dict[str, Any]], 
                          current_skills: List[Dict[str, Any]], time_frame: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a personalized learning path to acquire target skills.
    
    Args:
        user_id: ID of the user
        target_skills: List of skills the user wants to acquire
        current_skills: List of skills the user already has
        time_frame: Optional time frame for completing the learning path
        
    Returns:
        Dictionary with learning path details
    """
    logger.info(f"Generating learning path for user {user_id} with {len(target_skills)} target skills")
    
    # Use the existing mock function
    return generate_mock_learning_path(user_id, target_skills, current_skills, time_frame)