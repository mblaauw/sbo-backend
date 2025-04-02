# matching_service/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import httpx
import os
import logging

from .database import get_db, engine
from . import models, schemas
from .mock_data import generate_mock_job_roles

# Initialize database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Skills Based Organization - Matching Service",
    description="Service for matching candidates with job roles based on skills",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Skills Service URL
SKILLS_SERVICE_URL = os.getenv("SKILLS_SERVICE_URL", "http://localhost:8801")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8803")

# Initialize with mock data if needed
@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    if db.query(models.JobRole).count() == 0:
        logging.info("Initializing database with mock job roles")
        job_roles = generate_mock_job_roles()
        for role in job_roles:
            db_role = models.JobRole(
                title=role["title"],
                description=role["description"],
                department=role["department"]
            )
            db.add(db_role)
            db.flush()  # To get the role ID
            
            # Add required skills for this role
            for skill_req in role["required_skills"]:
                db_skill_req = models.RoleSkillRequirement(
                    role_id=db_role.id,
                    skill_id=skill_req["skill_id"],
                    importance=skill_req["importance"],
                    minimum_proficiency=skill_req["minimum_proficiency"]
                )
                db.add(db_skill_req)
        
        db.commit()

# Endpoint to get all job roles
@app.get("/roles", response_model=List[schemas.JobRole])
def get_all_roles(
    department: str = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    query = db.query(models.JobRole)
    if department:
        query = query.filter(models.JobRole.department == department)
    
    roles = query.offset(skip).limit(limit).all()
    return roles

# Endpoint to get a specific job role by ID
@app.get("/roles/{role_id}", response_model=schemas.JobRoleDetail)
def get_role(role_id: int, db: Session = Depends(get_db)):
    role = db.query(models.JobRole).filter(models.JobRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Get skill requirements for this role
    skill_requirements = db.query(models.RoleSkillRequirement).filter(
        models.RoleSkillRequirement.role_id == role_id
    ).all()
    
    # Get skill details from Skills Service
    skill_ids = [req.skill_id for req in skill_requirements]
    skill_details = {}
    
    # In a real implementation, we would call the Skills Service
    # Here we'll mock the response for simplicity
    for skill_id in skill_ids:
        skill_details[skill_id] = {
            "id": skill_id,
            "name": f"Skill {skill_id}",
            "description": f"Description for skill {skill_id}"
        }
    
    # Construct response
    requirements = []
    for req in skill_requirements:
        skill_detail = skill_details.get(req.skill_id, {"name": f"Unknown Skill {req.skill_id}"})
        requirements.append(
            schemas.SkillRequirementDetail(
                skill_id=req.skill_id,
                skill_name=skill_detail.get("name", ""),
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

# Endpoint to perform skill matching between a candidate and a role
@app.post("/match/candidate-role", response_model=schemas.MatchResult)
async def match_candidate_to_role(match_request: schemas.MatchRequest, db: Session = Depends(get_db)):
    # Get role details with skill requirements
    role = db.query(models.JobRole).filter(models.JobRole.id == match_request.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    skill_requirements = db.query(models.RoleSkillRequirement).filter(
        models.RoleSkillRequirement.role_id == match_request.role_id
    ).all()
    
    # Get candidate skills from User Service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{USER_SERVICE_URL}/users/{match_request.candidate_id}/skills")
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to retrieve candidate skills"
                )
            candidate_skills = response.json()
    except httpx.RequestError:
        # For this prototype, we'll use mock data if the service is unavailable
        candidate_skills = [
            {"skill_id": 1, "proficiency": 4},
            {"skill_id": 2, "proficiency": 3},
            {"skill_id": 3, "proficiency": 5},
            {"skill_id": 7, "proficiency": 2},
        ]
    
    # Convert to dictionary for easier lookup
    candidate_skill_dict = {skill["skill_id"]: skill["proficiency"] for skill in candidate_skills}
    
    # Perform matching
    matches = []
    gaps = []
    excess = []
    total_importance = 0
    total_match_score = 0
    
    for req in skill_requirements:
        total_importance += req.importance
        
        if req.skill_id in candidate_skill_dict:
            candidate_proficiency = candidate_skill_dict[req.skill_id]
            
            # Calculate match percentage for this skill
            if candidate_proficiency >= req.minimum_proficiency:
                match_score = req.importance * 1.0  # Full match
                matches.append({
                    "skill_id": req.skill_id,
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
                "required_proficiency": req.minimum_proficiency,
                "candidate_proficiency": 0,
                "gap": req.minimum_proficiency,
                "importance": req.importance
            })
    
    # Check for excess skills (skills the candidate has that aren't required)
    for skill_id, proficiency in candidate_skill_dict.items():
        if skill_id not in [req.skill_id for req in skill_requirements]:
            excess.append({
                "skill_id": skill_id,
                "proficiency": proficiency
            })
    
    # Calculate overall match percentage
    overall_match = (total_match_score / total_importance) * 100 if total_importance > 0 else 0
    
    # Get details for skills from Skills Service
    # In a real implementation, we'd call the Skills Service API
    # For this prototype, we'll use simplified skill names
    for match in matches:
        match["skill_name"] = f"Skill {match['skill_id']}"
    
    for gap in gaps:
        gap["skill_name"] = f"Skill {gap['skill_id']}"
    
    for ex in excess:
        ex["skill_name"] = f"Skill {ex['skill_id']}"
    
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

# Endpoint to find best matching candidates for a role
@app.get("/match/role-candidates/{role_id}", response_model=List[schemas.CandidateMatch])
async def find_candidates_for_role(
    role_id: int, 
    min_match_percentage: float = 60.0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    # Get role details
    role = db.query(models.JobRole).filter(models.JobRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # In a real implementation, we would:
    # 1. Get all candidates from User Service
    # 2. Get their skills
    # 3. Perform matching for each candidate
    # 4. Sort and return best matches
    
    # For this prototype, we'll return mock data
    return [
        schemas.CandidateMatch(
            candidate_id=1,
            candidate_name="John Doe",
            match_percentage=93.0,
            skill_matches=5,
            skill_gaps=1,
            excess_skills=2
        ),
        schemas.CandidateMatch(
            candidate_id=2,
            candidate_name="Jane Smith",
            match_percentage=88.0,
            skill_matches=4,
            skill_gaps=1,
            excess_skills=3
        ),
        schemas.CandidateMatch(
            candidate_id=3,
            candidate_name="Michael Johnson",
            match_percentage=87.0,
            skill_matches=4,
            skill_gaps=2,
            excess_skills=1
        )
    ]

# Endpoint to find best matching roles for a candidate
@app.get("/match/candidate-roles/{candidate_id}", response_model=List[schemas.RoleMatch])
async def find_roles_for_candidate(
    candidate_id: int,
    min_match_percentage: float = 60.0,
    department: str = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    # In a real implementation, we would:
    # 1. Get candidate skills from User Service
    # 2. Get all relevant roles from database
    # 3. Perform matching for each role
    # 4. Sort and return best matches
    
    # For this prototype, we'll return mock data
    query = db.query(models.JobRole)
    if department:
        query = query.filter(models.JobRole.department == department)
    
    roles = query.limit(3).all()  # Get a few roles for demo purposes
    
    return [
        schemas.RoleMatch(
            role_id=roles[0].id if len(roles) > 0 else 1,
            role_title=roles[0].title if len(roles) > 0 else "Software Engineer",
            department=roles[0].department if len(roles) > 0 else "IT",
            match_percentage=85.0,
            skill_matches=6,
            skill_gaps=2,
            required_training="2 weeks"
        ),
        schemas.RoleMatch(
            role_id=roles[1].id if len(roles) > 1 else 2,
            role_title=roles[1].title if len(roles) > 1 else "Product Manager",
            department=roles[1].department if len(roles) > 1 else "Product",
            match_percentage=78.0,
            skill_matches=5,
            skill_gaps=3,
            required_training="4 weeks"
        ),
        schemas.RoleMatch(
            role_id=roles[2].id if len(roles) > 2 else 3,
            role_title=roles[2].title if len(roles) > 2 else "Data Analyst",
            department=roles[2].department if len(roles) > 2 else "Data",
            match_percentage=72.0,
            skill_matches=4,
            skill_gaps=3,
            required_training="6 weeks"
        )
    ]


