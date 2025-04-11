"""
Functions to initialize the database with mock data.
"""

import logging
from sqlalchemy.orm import Session
from datetime import datetime

from models import (
    SkillCategory, Skill, User, UserSkill, JobRole, 
    RoleSkillRequirement, Assessment, AssessmentQuestion
)
from mock_data import (
    get_mock_skills_taxonomy, get_mock_users, 
    get_mock_job_roles, get_mock_assessments
)

logger = logging.getLogger("sbo.init_mock_data")

def init_mock_data_if_needed(db: Session):
    """Initialize database with mock data if tables are empty"""
    # Initialize skills taxonomy
    init_skills_taxonomy_if_needed(db)
    
    # Initialize users
    init_users_if_needed(db)
    
    # Initialize job roles
    init_job_roles_if_needed(db)
    
    # Initialize assessments
    init_assessments_if_needed(db)

def init_skills_taxonomy_if_needed(db: Session):
    """Initialize skills taxonomy if empty"""
    if db.query(Skill).count() == 0:
        logger.info("Initializing database with mock skills taxonomy")
        skills_data = get_mock_skills_taxonomy()
        
        # Add skill categories
        for category in skills_data.get("categories", []):
            db_category = SkillCategory(**category)
            db.add(db_category)
        
        db.commit()
        
        # Add skills
        for skill in skills_data.get("skills", []):
            db_skill = Skill(**skill)
            db.add(db_skill)
        
        db.commit()
        logger.info(f"Added {len(skills_data.get('skills', []))} skills and {len(skills_data.get('categories', []))} categories")

def init_users_if_needed(db: Session):
    """Initialize users if empty"""
    if db.query(User).count() == 0:
        logger.info("Initializing database with mock users")
        users_data = get_mock_users()
        
        for user_data in users_data:
            # Extract skills before creating user
            skills_data = user_data.pop("skills", [])
            
            # Create user
            db_user = User(**user_data)
            db.add(db_user)
            db.flush()  # To get the user ID
            
            # Add skills
            for skill_data in skills_data:
                user_skill = UserSkill(
                    user_id=db_user.id,
                    **skill_data
                )
                db.add(user_skill)
        
        db.commit()
        logger.info(f"Added {len(users_data)} users")

def init_job_roles_if_needed(db: Session):
    """Initialize job roles if empty"""
    if db.query(JobRole).count() == 0:
        logger.info("Initializing database with mock job roles")
        roles_data = get_mock_job_roles()
        
        for role_data in roles_data:
            # Extract required skills before creating role
            required_skills = role_data.pop("required_skills", [])
            
            # Create role
            db_role = JobRole(**role_data)
            db.add(db_role)
            db.flush()  # To get the role ID
            
            # Add required skills
            for skill_req in required_skills:
                db_skill_req = RoleSkillRequirement(
                    role_id=db_role.id,
                    **skill_req
                )
                db.add(db_skill_req)
        
        db.commit()
        logger.info(f"Added {len(roles_data)} job roles")

def init_assessments_if_needed(db: Session):
    """Initialize assessments if empty"""
    if db.query(Assessment).count() == 0:
        logger.info("Initializing database with mock assessments")
        assessments_data = get_mock_assessments()
        
        for assessment_data in assessments_data:
            # Extract questions before creating assessment
            questions_data = assessment_data.pop("questions", [])
            
            # Create assessment
            db_assessment = Assessment(**assessment_data)
            db.add(db_assessment)
            db.flush()  # To get the assessment ID
            
            # Add questions
            for question_data in questions_data:
                db_question = AssessmentQuestion(
                    assessment_id=db_assessment.id,
                    **question_data
                )
                db.add(db_question)
        
        db.commit()
        logger.info(f"Added {len(assessments_data)} assessments")