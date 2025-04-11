"""
Matching service endpoints for SBO application.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from database import get_db
from middleware import get_current_user, User
from models import (
    JobRole, RoleSkillRequirement, UserSkill, Skill, User as UserModel,
    MatchHistory
)
import schemas

router = APIRouter(tags=["matching"])

@router.get("/roles", response_model=List[schemas.JobRole])
def get_all_roles(
    department: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100, 
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all job roles with optional filtering"""
    query = db.query(JobRole)
    
    if department:
        query = query.filter(JobRole.department == department)
    
    roles = query.offset(skip).limit(limit).all()
    return roles

@router.get("/roles/{role_id}", response_model=schemas.JobRoleDetail)
def get_role(
    role_id: int, 
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific job role by ID"""
    role = db.query(JobRole).filter(JobRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Get skill requirements for this role
    skill_requirements = db.query(RoleSkillRequirement).filter(
        RoleSkillRequirement.role_id == role_id
    ).all()
    
    # Get skill details
    requirements = []
    for req in skill_requirements:
        skill = db.query(Skill).filter(Skill.id == req.skill_id).first()
        if not skill:
            continue  # Skip if skill not found
        
        requirements.append(
            schemas.SkillRequirementDetail(
                skill_id=req.skill_id,
                skill_name=skill.name,
                importance=req.importance,
                minimum_proficiency=req.minimum_proficiency
            )
        )
    
    return schemas.JobRoleDetail(
        id=role.id,
        title=role.title,
        description=role.description,
        department=role.department,
        required_skills=requirements
    )

@router.post("/match/candidate-role", response_model=schemas.MatchResult)
def match_candidate_to_role(
    match_request: schemas.MatchRequest, 
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Match a candidate to a job role based on skills"""
    try:
        # Get role details with skill requirements
        role = db.query(JobRole).filter(JobRole.id == match_request.role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Check if candidate exists
        candidate = db.query(UserModel).filter(UserModel.id == match_request.candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        skill_requirements = db.query(RoleSkillRequirement).filter(
            RoleSkillRequirement.role_id == match_request.role_id
        ).all()
        
        # Get candidate skills
        candidate_skills = db.query(UserSkill).filter(
            UserSkill.user_id == match_request.candidate_id
        ).all()
        
        if not candidate_skills:
            raise HTTPException(status_code=404, detail="Candidate has no skills recorded")
        
        # Convert to dictionary for easier lookup
        candidate_skill_dict = {skill.skill_id: skill.proficiency_level for skill in candidate_skills}
        
        # Perform matching
        matches = []
        gaps = []
        excess = []
        total_importance = 0
        total_match_score = 0
        
        for req in skill_requirements:
            total_importance += req.importance
            
            # Get skill details
            skill = db.query(Skill).filter(Skill.id == req.skill_id).first()
            skill_name = skill.name if skill else f"Skill {req.skill_id}"
            
            if req.skill_id in candidate_skill_dict:
                candidate_proficiency = candidate_skill_dict[req.skill_id]
                
                # Calculate match percentage for this skill
                if candidate_proficiency >= req.minimum_proficiency:
                    match_score = req.importance * 1.0  # Full match
                    matches.append({
                        "skill_id": req.skill_id,
                        "skill_name": skill_name,
                        "required_proficiency": req.minimum_proficiency,
                        "candidate_proficiency": candidate_proficiency,
                        "importance": req.importance
                    })
                else:
                    # Partial match - calculate percentage
                    match_percentage = candidate_proficiency / req.minimum_proficiency
                    match_score = req.importance * match_percentage
                    
                    gaps.append({
                        "skill_id": req.skill_id,
                        "skill_name": skill_name,
                        "required_proficiency": req.minimum_proficiency,
                        "candidate_proficiency": candidate_proficiency,
                        "gap": req.minimum_proficiency - candidate_proficiency,
                        "importance": req.importance
                    })
                
                total_match_score += match_score
            else:
                # Missing skill
                gaps.append({
                    "skill_id": req.skill_id,
                    "skill_name": skill_name,
                    "required_proficiency": req.minimum_proficiency,
                    "candidate_proficiency": 0,
                    "gap": req.minimum_proficiency,
                    "importance": req.importance
                })
        
        # Check for excess skills (skills the candidate has that aren't required)
        for skill_id, proficiency in candidate_skill_dict.items():
            if skill_id not in [req.skill_id for req in skill_requirements]:
                skill = db.query(Skill).filter(Skill.id == skill_id).first()
                skill_name = skill.name if skill else f"Skill {skill_id}"
                
                excess.append({
                    "skill_id": skill_id,
                    "skill_name": skill_name,
                    "proficiency": proficiency
                })
        
        # Calculate overall match percentage
        overall_match = (total_match_score / total_importance) * 100 if total_importance > 0 else 0
        
        # Prepare training recommendations for gaps
        training_recommendations = []
        for gap in gaps:
            training_recommendations.append({
                "skill_id": gap["skill_id"],
                "skill_name": gap["skill_name"],
                "current_level": gap["candidate_proficiency"],
                "target_level": gap["required_proficiency"],
                "training_type": "Course" if gap["gap"] > 2 else "On-the-job training",
                "estimated_duration": f"{gap['gap'] * 2} weeks"
            })
        
        # Save match history
        try:
            match_history = MatchHistory(
                candidate_id=match_request.candidate_id,
                role_id=match_request.role_id,
                match_percentage=overall_match,
                match_date=datetime.now()
            )
            db.add(match_history)
            db.commit()
        except Exception as e:
            db.rollback()
            # Log error but continue - this shouldn't block the response
            print(f"Error saving match history: {str(e)}")
        
        return schemas.MatchResult(
            candidate_id=match_request.candidate_id,
            role_id=match_request.role_id,
            role_title=role.title,
            overall_match_percentage=overall_match,
            skill_matches=matches,
            skill_gaps=gaps,
            excess_skills=excess,
            training_recommendations=training_recommendations
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error matching candidate to role: {str(e)}")

@router.get("/match/role-candidates/{role_id}", response_model=List[schemas.CandidateMatch])
def find_candidates_for_role(
    role_id: int, 
    min_match_percentage: float = 60.0,
    limit: int = 10,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Find best matching candidates for a job role"""
    try:
        # Get role details
        role = db.query(JobRole).filter(JobRole.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Get all users
        users = db.query(UserModel).all()
        
        # Process each candidate
        candidates_matches = []
        
        for candidate in users:
            # Calculate match (simplified for performance)
            # In a real implementation, we would calculate matches more efficiently
            
            # Get candidate skills
            candidate_skills = db.query(UserSkill).filter(UserSkill.user_id == candidate.id).all()
            if not candidate_skills:
                continue  # Skip candidates with no skills
            
            # Get role skill requirements
            skill_requirements = db.query(RoleSkillRequirement).filter(
                RoleSkillRequirement.role_id == role_id
            ).all()
            
            # Calculate match score (simplified version)
            candidate_skill_dict = {skill.skill_id: skill.proficiency_level for skill in candidate_skills}
            
            matches = 0
            gaps = 0
            excess = len(candidate_skills)
            total_importance = 0
            total_match_score = 0
            
            for req in skill_requirements:
                total_importance += req.importance
                excess -= 1 if req.skill_id in candidate_skill_dict else 0
                
                if req.skill_id in candidate_skill_dict:
                    candidate_proficiency = candidate_skill_dict[req.skill_id]
                    
                    if candidate_proficiency >= req.minimum_proficiency:
                        # Full match
                        matches += 1
                        total_match_score += req.importance
                    else:
                        # Gap
                        gaps += 1
                        # Partial credit for partially matching
                        total_match_score += req.importance * (candidate_proficiency / req.minimum_proficiency)
                else:
                    # Missing skill
                    gaps += 1
            
            # Calculate overall match percentage
            overall_match = (total_match_score / total_importance) * 100 if total_importance > 0 else 0
            
            # Only include candidates above minimum match percentage
            if overall_match >= min_match_percentage:
                candidates_matches.append(
                    schemas.CandidateMatch(
                        candidate_id=candidate.id,
                        candidate_name=candidate.full_name,
                        match_percentage=overall_match,
                        skill_matches=matches,
                        skill_gaps=gaps,
                        excess_skills=excess
                    )
                )
        
        # Sort by match percentage (descending) and limit results
        candidates_matches.sort(key=lambda x: x.match_percentage, reverse=True)
        return candidates_matches[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding candidates for role: {str(e)}")

@router.get("/match/candidate-roles/{candidate_id}", response_model=List[schemas.RoleMatch])
def find_roles_for_candidate(
    candidate_id: int,
    min_match_percentage: float = 60.0,
    department: Optional[str] = None,
    limit: int = 10,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Find best matching roles for a candidate"""
    try:
        # Get candidate
        candidate = db.query(UserModel).filter(UserModel.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Get candidate skills
        candidate_skills = db.query(UserSkill).filter(UserSkill.user_id == candidate_id).all()
        if not candidate_skills:
            raise HTTPException(status_code=404, detail="Candidate has no skills recorded")
        
        candidate_skill_dict = {skill.skill_id: skill.proficiency_level for skill in candidate_skills}
        
        # Get relevant roles
        query = db.query(JobRole)
        if department:
            query = query.filter(JobRole.department == department)
        
        roles = query.all()
        
        # Process each role
        role_matches = []
        
        for role in roles:
            # Get role skill requirements
            skill_requirements = db.query(RoleSkillRequirement).filter(
                RoleSkillRequirement.role_id == role.id
            ).all()
            
            # Calculate match score
            matches = 0
            gaps = 0
            total_importance = 0
            total_match_score = 0
            total_training_weeks = 0
            
            for req in skill_requirements:
                total_importance += req.importance
                
                if req.skill_id in candidate_skill_dict:
                    candidate_proficiency = candidate_skill_dict[req.skill_id]
                    
                    if candidate_proficiency >= req.minimum_proficiency:
                        # Full match
                        matches += 1
                        total_match_score += req.importance
                    else:
                        # Gap
                        gaps += 1
                        # Calculate training needed
                        proficiency_gap = req.minimum_proficiency - candidate_proficiency
                        total_training_weeks += proficiency_gap * 2  # Estimate 2 weeks per level
                        # Partial credit for partially matching
                        total_match_score += req.importance * (candidate_proficiency / req.minimum_proficiency)
                else:
                    # Missing skill
                    gaps += 1
                    # Calculate training needed
                    total_training_weeks += req.minimum_proficiency * 3  # More time for new skills
            
            # Calculate overall match percentage
            overall_match = (total_match_score / total_importance) * 100 if total_importance > 0 else 0
            
            # Only include roles above minimum match percentage
            if overall_match >= min_match_percentage:
                role_matches.append(
                    schemas.RoleMatch(
                        role_id=role.id,
                        role_title=role.title,
                        department=role.department,
                        match_percentage=overall_match,
                        skill_matches=matches,
                        skill_gaps=gaps,
                        required_training=f"{total_training_weeks} weeks"
                    )
                )
        
        # Sort by match percentage (descending) and limit results
        role_matches.sort(key=lambda x: x.match_percentage, reverse=True)
        return role_matches[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding roles for candidate: {str(e)}")