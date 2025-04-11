# llm_service/llm_client.py
import os
import json
import logging
from typing import List, Dict, Any
import random

# In a real implementation, this would use an actual LLM API
# For this prototype, we'll mock the responses

def extract_skills_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extract skills from unstructured text using an LLM.
    
    Args:
        text: The text to extract skills from
        
    Returns:
        A list of extracted skills with confidence scores and context
    """
    # For the prototype, we'll simulate LLM extraction with predefined skills
    sample_skills = [
        "communication",
        "project management",
        "data analysis",
        "leadership",
        "problem solving",
        "teamwork",
        "programming",
        "public speaking",
        "writing",
        "critical thinking"
    ]
    
    # Mock extraction by randomly selecting skills and generating confidence scores
    text_lower = text.lower()
    extracted_skills = []
    
    for skill in sample_skills:
        if skill in text_lower or random.random() < 0.3:  # Randomly include some skills
            confidence = round(random.uniform(0.7, 0.98), 2)
            context = text[max(0, text_lower.find(skill) - 50):min(len(text), text_lower.find(skill) + 50)] if skill in text_lower else ""
            
            extracted_skills.append({
                "skill_name": skill,
                "confidence": confidence,
                "context": context
            })
    
    return extracted_skills

def map_skills_to_taxonomy(skills: List[str], taxonomy: List[str]) -> List[Dict[str, Any]]:
    """
    Map free-text skills to a standardized taxonomy using an LLM.
    
    Args:
        skills: List of skill names to map
        taxonomy: List of standardized skill names in the taxonomy
        
    Returns:
        A list of mapped skills with confidence scores
    """
    # Mock mapping with simple string matching and random confidence
    mapped_skills = []
    
    for skill in skills:
        best_match = None
        highest_similarity = 0
        
        for tax_skill in taxonomy:
            # Simple string similarity - in a real implementation, use embedding similarity
            similarity = len(set(skill.lower().split()) & set(tax_skill.lower().split())) / max(len(skill.split()), len(tax_skill.split()))
            
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = tax_skill
        
        if highest_similarity > 0.3 or random.random() < 0.8:  # Usually find a match
            confidence = max(0.5, highest_similarity)
            skill_id = taxonomy.index(best_match) + 1  # Mock ID generation
            
            mapped_skills.append({
                "original_text": skill,
                "skill_id": skill_id,
                "skill_name": best_match,
                "confidence": round(confidence, 2)
            })
        else:
            # No good match found - map to a random skill with low confidence
            random_skill = random.choice(taxonomy)
            skill_id = taxonomy.index(random_skill) + 1
            
            mapped_skills.append({
                "original_text": skill,
                "skill_id": skill_id,
                "skill_name": random_skill,
                "confidence": round(random.uniform(0.3, 0.5), 2)
            })
    
    return mapped_skills

def generate_assessment_questions(
    skill_name: str,
    skill_description: str = None,
    num_questions: int = 5,
    difficulty: str = "medium"
) -> List[Dict[str, Any]]:
    """
    Generate assessment questions for a specific skill using an LLM.
    
    Args:
        skill_name: The name of the skill to generate questions for
        skill_description: Optional description of the skill
        num_questions: Number of questions to generate
        difficulty: Difficulty level ("easy", "medium", "hard")
        
    Returns:
        A list of assessment questions with options and correct answers
    """
    # Mock question generation
    questions = []
    
    # Dictionary of question templates by skill
    question_templates = {
        "communication": [
            "What is the most effective way to communicate complex information to a non-technical audience?",
            "When delivering bad news to a team, what approach is most appropriate?",
            "Which of the following is an example of active listening?",
            "What strategy is most effective for resolving a communication conflict?",
            "In a cross-cultural communication context, which factor is most important to consider?"
        ],
        "project management": [
            "What is the critical path in project management?",
            "Which project management methodology is best suited for projects with changing requirements?",
            "What is the purpose of a project kickoff meeting?",
            "How should a project manager address scope creep?",
            "What is the primary purpose of a Gantt chart?"
        ],
        "data analysis": [
            "Which statistical measure is most appropriate for analyzing skewed data?",
            "What is the purpose of data normalization?",
            "Which visualization is best for comparing values across multiple categories?",
            "What is the difference between correlation and causation?",
            "Which sampling method would be most appropriate for a heterogeneous population?"
        ]
    }
    
    # Get templates for the skill or use generic templates
    templates = question_templates.get(skill_name.lower(), [
        f"What is the most important aspect of {skill_name}?",
        f"Which approach to {skill_name} is most effective in a team environment?",
        f"What is a common misconception about {skill_name}?",
        f"How would you measure proficiency in {skill_name}?",
        f"What is the relationship between {skill_name} and organizational performance?"
    ])
    
    # Generate questions based on templates
    for i in range(min(num_questions, len(templates))):
        question = templates[i]
        
        # Generate options
        options = [
            f"Option A for {question}",
            f"Option B for {question}",
            f"Option C for {question}",
            f"Option D for {question}"
        ]
        
        # Randomly select correct answer
        correct_answer = random.randint(0, 3)
        
        questions.append({
            "question": question,
            "options": options,
            "correct_answer_index": correct_answer,
            "explanation": f"Explanation for why option {chr(65 + correct_answer)} is correct for {question}."
        })
    
    return questions

def analyze_resume(resume_text: str) -> Dict[str, Any]:
    """
    Analyze a resume to extract skills, experience, and education.
    
    Args:
        resume_text: The text content of the resume
        
    Returns:
        A dictionary containing extracted information
    """
    # Mock resume analysis
    # Extract potential skills
    skills = extract_skills_from_text(resume_text)
    
    # Mock experiences based on common job titles
    experiences = []
    job_titles = ["Software Engineer", "Project Manager", "Data Analyst", "Marketing Specialist"]
    companies = ["Tech Corp", "Innovative Solutions", "Data Insights", "Marketing Pro"]
    
    for i in range(random.randint(1, 4)):
        title = random.choice(job_titles)
        company = random.choice(companies)
        
        # Assign relevant skills to each experience
        job_skills = []
        for skill in skills:
            if random.random() < 0.5:  # 50% chance to include each skill
                job_skills.append(skill["skill_name"])
        
        experiences.append({
            "title": title,
            "company": company,
            "duration": f"{random.randint(1, 5)} years",
            "description": f"Worked as a {title} at {company}, responsible for various projects and initiatives.",
            "skills": job_skills
        })
    
    # Mock education
    education = [
        {
            "degree": "Bachelor's Degree",
            "field": "Computer Science",
            "institution": "State University",
            "year": str(random.randint(2000, 2020))
        }
    ]
    
    # Generate suggested roles based on extracted skills
    role_mapping = {
        "communication": ["Communications Specialist", "Public Relations Manager"],
        "project management": ["Project Manager", "Program Coordinator"],
        "data analysis": ["Data Analyst", "Business Intelligence Specialist"],
        "leadership": ["Team Lead", "Department Manager"],
        "programming": ["Software Developer", "Web Developer"],
        "public speaking": ["Trainer", "Presenter"],
        "writing": ["Content Writer", "Technical Writer"]
    }
    
    suggested_roles = []
    for skill in skills:
        skill_name = skill["skill_name"].lower()
        if skill_name in role_mapping and random.random() < 0.7:
            suggested_roles.extend(role_mapping[skill_name])
    
    # Remove duplicates and limit to 5 roles
    suggested_roles = list(set(suggested_roles))[:5]
    
    return {
        "skills": skills,
        "experiences": experiences,
        "education": education,
        "summary": f"Experienced professional with skills in {', '.join([s['skill_name'] for s in skills[:3]])}.",
        "suggested_roles": suggested_roles
    }

def generate_learning_path(
    user_id: int,
    target_skills: List[Dict[str, Any]],
    current_skills: List[Dict[str, Any]],
    time_frame: str = None
) -> Dict[str, Any]:
    """
    Generate a personalized learning path to acquire target skills.
    
    Args:
        user_id: The ID of the user
        target_skills: List of skills the user wants to acquire
        current_skills: List of skills the user already has
        time_frame: Optional time constraint
        
    Returns:
        A structured learning path
    """
    # Mock learning path generation
    steps = []
    
    # Create a set of current skill names for easy lookup
    current_skill_names = {skill["name"].lower() for skill in current_skills}
    
    # Filter target skills to those not already possessed
    new_target_skills = [skill for skill in target_skills 
                         if skill["name"].lower() not in current_skill_names]
    
    if not new_target_skills:
        # If all target skills are already possessed, suggest advanced learning
        steps = [
            {
                "name": "Advanced Skill Enhancement",
                "description": "Deepen your existing skills through practical application.",
                "duration": "4 weeks",
                "resources": [
                    {"type": "course", "name": "Advanced Applications in Your Field"}
                ],
                "skills_addressed": [skill["name"] for skill in current_skills[:3]]
            }
        ]
    else:
        # Learning resources by skill type
        resource_templates = {
            "communication": [
                {"type": "course", "name": "Effective Communication in the Workplace"},
                {"type": "book", "name": "How to Win Friends and Influence People"},
                {"type": "workshop", "name": "Active Listening Workshop"}
            ],
            "data analysis": [
                {"type": "course", "name": "Introduction to Data Analysis"},
                {"type": "tutorial", "name": "Python for Data Analysis"},
                {"type": "project", "name": "Analyze a Real-World Dataset"}
            ],
            "project management": [
                {"type": "course", "name": "Project Management Fundamentals"},
                {"type": "certification", "name": "PMI Project Management Professional"},
                {"type": "workshop", "name": "Agile Project Management"}
            ]
        }
        
        # Generate steps for each target skill
        for skill in new_target_skills:
            skill_name = skill["name"].lower()
            
            # Get relevant resources or use generic ones
            resources = resource_templates.get(skill_name, [
                {"type": "course", "name": f"Introduction to {skill['name']}"},
                {"type": "book", "name": f"{skill['name']} in Practice"},
                {"type": "workshop", "name": f"Hands-on {skill['name']}"}
            ])
            
            # Select a subset of resources
            selected_resources = random.sample(resources, min(2, len(resources)))
            
            steps.append({
                "name": f"Learn {skill['name']}",
                "description": f"Develop proficiency in {skill['name']} through structured learning.",
                "duration": f"{random.randint(2, 8)} weeks",
                "resources": selected_resources,
                "skills_addressed": [skill["name"]]
            })
    
    # Calculate total duration
    total_weeks = sum([int(step["duration"].split()[0]) for step in steps])
    
    return {
        "user_id": user_id,
        "title": "Personalized Skill Development Plan",
        "description": f"A customized learning path to help you acquire {len(new_target_skills)} new skills.",
        "total_duration": f"{total_weeks} weeks",
        "steps": steps
    }