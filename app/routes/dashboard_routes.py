"""
Dashboard endpoints for SBO application.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime

from database import get_db
from middleware import get_current_user, User, admin_required
from models import User as UserModel, JobRole, Assessment, UserSkill, RoleSkillRequirement
import schemas

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/candidate/{candidate_id}")
def get_candidate_dashboard(
    candidate_id: int, 
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard data for a candidate"""
    try:
        # Check if candidate exists
        candidate = db.query(UserModel).filter(UserModel.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Security check - only admins can view other users' dashboards
        if str(candidate_id) != user.id and user.role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to view this dashboard")
            
        # Get candidate profile
        profile = {
            "id": candidate.id,
            "username": candidate.username,
            "email": candidate.email,
            "full_name": candidate.full_name,
            "department": candidate.department,
            "title": candidate.title,
            "bio": candidate.bio,
            "created_at": candidate.created_at
        }
        
        # Get candidate skills
        skills_query = db.query(
            UserSkill, models.Skill, models.SkillCategory
        ).join(
            models.Skill, UserSkill.skill_id == models.Skill.id
        ).join(
            models.SkillCategory, models.Skill.category_id == models.SkillCategory.id
        ).filter(
            UserSkill.user_id == candidate_id
        )
        
        skills_data = []
        for user_skill, skill, category in skills_query.all():
            skills_data.append({
                "skill_id": skill.id,
                "skill_name": skill.name,
                "category_id": category.id,
                "category_name": category.name,
                "proficiency_level": user_skill.proficiency_level,
                "is_verified": user_skill.is_verified,
                "source": user_skill.source,
                "last_verified": user_skill.last_verified
            })
            
        # Get matching roles with direct DB queries for efficiency
        candidate_skill_dict = {skill["skill_id"]: skill["proficiency_level"] for skill in skills_data}
        
        # Fetch all roles
        roles = db.query(JobRole).limit(20).all()
        
        # Calculate match for each role
        role_matches = []
        for role in roles:
            requirements = db.query(RoleSkillRequirement).filter(
                RoleSkillRequirement.role_id == role.id
            ).all()
            
            total_importance = 0
            total_match_score = 0
            matches = 0
            gaps = 0
            
            for req in requirements:
                total_importance += req.importance
                
                if req.skill_id in candidate_skill_dict:
                    candidate_proficiency = candidate_skill_dict[req.skill_id]
                    
                    if candidate_proficiency >= req.minimum_proficiency:
                        matches += 1
                        total_match_score += req.importance
                    else:
                        gaps += 1
                        # Partial credit for partial match
                        match_ratio = candidate_proficiency / req.minimum_proficiency
                        total_match_score += req.importance * match_ratio
                else:
                    gaps += 1
            
            overall_match = (total_match_score / total_importance * 100) if total_importance > 0 else 0
            
            # Only include roles with match above 50%
            if overall_match >= 50:
                role_matches.append({
                    "role_id": role.id,
                    "role_title": role.title,
                    "department": role.department,
                    "match_percentage": round(overall_match, 1),
                    "skill_matches": matches,
                    "skill_gaps": gaps
                })
                
        # Sort by match percentage (descending)
        role_matches.sort(key=lambda x: x["match_percentage"], reverse=True)
        
        # Get recent assessment results
        assessment_results = db.query(
            models.AssessmentResult, Assessment
        ).join(
            Assessment, models.AssessmentResult.assessment_id == Assessment.id
        ).filter(
            models.AssessmentResult.user_id == candidate_id
        ).order_by(
            models.AssessmentResult.completed_at.desc()
        ).limit(5).all()
        
        assessment_data = []
        for result, assessment in assessment_results:
            assessment_data.append({
                "id": result.id,
                "assessment_id": result.assessment_id,
                "assessment_title": assessment.title,
                "skill_id": assessment.skill_id,
                "score": result.score,
                "proficiency_level": result.proficiency_level,
                "completed_at": result.completed_at
            })
        
        # Calculate skill statistics
        skill_stats = {
            "total_skills": len(skills_data),
            "verified_skills": sum(1 for skill in skills_data if skill["is_verified"]),
            "avg_proficiency": sum(skill["proficiency_level"] for skill in skills_data) / len(skills_data) if skills_data else 0,
            "skill_distribution": {}
        }
        
        # Count skills by category
        for skill in skills_data:
            category = skill["category_name"]
            if category not in skill_stats["skill_distribution"]:
                skill_stats["skill_distribution"][category] = 0
            skill_stats["skill_distribution"][category] += 1
        
        # Combine data for dashboard
        dashboard_data = {
            "candidate": profile,
            "skills": skills_data,
            "skill_statistics": skill_stats,
            "matching_roles": role_matches[:5],  # Top 5 matches
            "assessment_results": assessment_data,
            "generated_at": datetime.now().isoformat()
        }
        
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating candidate dashboard: {str(e)}")

@router.get("/role/{role_id}")
def get_role_dashboard(
    role_id: int, 
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard data for a job role"""
    try:
        # Check if role exists
        role = db.query(JobRole).filter(JobRole.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Get role details
        role_details = {
            "id": role.id,
            "title": role.title,
            "description": role.description,
            "department": role.department
        }
        
        # Get skill requirements
        requirements_query = db.query(
            RoleSkillRequirement, models.Skill
        ).join(
            models.Skill, RoleSkillRequirement.skill_id == models.Skill.id
        ).filter(
            RoleSkillRequirement.role_id == role_id
        )
        
        required_skills = []
        for req, skill in requirements_query.all():
            required_skills.append({
                "skill_id": req.skill_id,
                "skill_name": skill.name,
                "importance": req.importance,
                "minimum_proficiency": req.minimum_proficiency
            })
            
        # Find matching candidates
        skill_ids = [req["skill_id"] for req in required_skills]
        
        # Get all users with at least one matching skill
        user_query = db.query(UserModel).join(
            UserSkill, UserModel.id == UserSkill.user_id
        ).filter(
            UserSkill.skill_id.in_(skill_ids)
        ).distinct()
        
        users = user_query.all()
        
        # Calculate match for each candidate
        candidate_matches = []
        for candidate in users:
            # Get candidate skills
            candidate_skills = db.query(UserSkill).filter(
                UserSkill.user_id == candidate.id
            ).all()
            
            candidate_skill_dict = {skill.skill_id: skill.proficiency_level for skill in candidate_skills}
            
            total_importance = 0
            total_match_score = 0
            matches = 0
            gaps = 0
            excess = 0
            
            for req in required_skills:
                skill_id = req["skill_id"]
                min_proficiency = req["minimum_proficiency"]
                importance = req["importance"]
                
                total_importance += importance
                
                if skill_id in candidate_skill_dict:
                    proficiency = candidate_skill_dict[skill_id]
                    if proficiency >= min_proficiency:
                        matches += 1
                        total_match_score += importance
                    else:
                        gaps += 1
                        match_ratio = proficiency / min_proficiency
                        total_match_score += importance * match_ratio
                else:
                    gaps += 1
            
            # Count excess skills
            for skill_id in candidate_skill_dict:
                if skill_id not in skill_ids:
                    excess += 1
            
            overall_match = (total_match_score / total_importance * 100) if total_importance > 0 else 0
            
            # Only include candidates with match above 50%
            if overall_match >= 50:
                candidate_matches.append({
                    "candidate_id": candidate.id,
                    "candidate_name": candidate.full_name,
                    "department": candidate.department,
                    "title": candidate.title,
                    "match_percentage": round(overall_match, 1),
                    "skill_matches": matches,
                    "skill_gaps": gaps,
                    "excess_skills": excess
                })
        
        # Sort by match percentage (descending)
        candidate_matches.sort(key=lambda x: x["match_percentage"], reverse=True)
        
        # Skill gap analysis - identify most common missing skills
        all_candidate_ids = [candidate.id for candidate in users]
        all_candidate_skills = db.query(UserSkill).filter(
            UserSkill.user_id.in_(all_candidate_ids)
        ).all()
        
        skill_coverage = {req["skill_id"]: 0 for req in required_skills}
        for skill in all_candidate_skills:
            if skill.skill_id in skill_coverage:
                skill_coverage[skill.skill_id] += 1
        
        # Calculate percentage coverage for each skill
        skill_gap_analysis = []
        for req in required_skills:
            skill_id = req["skill_id"]
            coverage = (skill_coverage[skill_id] / len(users) * 100) if users else 0
            skill_gap_analysis.append({
                "skill_id": skill_id,
                "skill_name": req["skill_name"],
                "coverage_percentage": round(coverage, 1),
                "importance": req["importance"]
            })
        
        # Sort by coverage (ascending) to highlight biggest gaps
        skill_gap_analysis.sort(key=lambda x: x["coverage_percentage"])
        
        # Combine data for dashboard
        dashboard_data = {
            "role": role_details,
            "required_skills": required_skills,
            "matching_candidates": candidate_matches[:5],  # Top 5 matches
            "skill_gap_analysis": skill_gap_analysis,
            "total_candidate_pool": len(users),
            "generated_at": datetime.now().isoformat()
        }
        
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating role dashboard: {str(e)}")

@router.get("/organization")
def get_organization_dashboard(
    user: User = Depends(admin_required),  # Only admins can access
    db: Session = Depends(get_db)
):
    """Get organization-wide dashboard with skills analysis"""
    try:
        # Count users by department
        dept_counts = {}
        departments = db.query(UserModel.department, db.func.count(UserModel.id)).group_by(
            UserModel.department
        ).all()
        
        for dept, count in departments:
            dept_counts[dept or "Unassigned"] = count
            
        # Count skills by category
        skill_counts = {}
        categories = db.query(
            models.SkillCategory.name, 
            db.func.count(models.Skill.id)
        ).join(
            models.Skill, models.SkillCategory.id == models.Skill.category_id
        ).group_by(
            models.SkillCategory.name
        ).all()
        
        for category, count in categories:
            skill_counts[category] = count
            
        # Get most common skills across organization
        common_skills = db.query(
            models.Skill.id,
            models.Skill.name,
            db.func.count(UserSkill.user_id).label('user_count')
        ).join(
            UserSkill, models.Skill.id == UserSkill.skill_id
        ).group_by(
            models.Skill.id, models.Skill.name
        ).order_by(
            db.desc('user_count')
        ).limit(10).all()
        
        top_skills = []
        total_users = db.query(UserModel).count()
        
        for skill_id, skill_name, user_count in common_skills:
            coverage = (user_count / total_users * 100) if total_users > 0 else 0
            top_skills.append({
                "skill_id": skill_id,
                "skill_name": skill_name,
                "user_count": user_count,
                "coverage_percentage": round(coverage, 1)
            })
            
        # Get skill gaps (skills required by roles but rare among users)
        role_skills = db.query(
            models.Skill.id,
            models.Skill.name,
            db.func.count(RoleSkillRequirement.role_id).label('role_count')
        ).join(
            RoleSkillRequirement, models.Skill.id == RoleSkillRequirement.skill_id
        ).group_by(
            models.Skill.id, models.Skill.name
        ).order_by(
            db.desc('role_count')
        ).limit(20).all()
        
        skill_gaps = []
        for skill_id, skill_name, role_count in role_skills:
            # Count users with this skill
            user_count = db.query(db.func.count(UserSkill.user_id)).filter(
                UserSkill.skill_id == skill_id
            ).scalar()
            
            if user_count < (total_users * 0.2):  # Less than 20% of users have this skill
                coverage = (user_count / total_users * 100) if total_users > 0 else 0
                skill_gaps.append({
                    "skill_id": skill_id,
                    "skill_name": skill_name,
                    "role_count": role_count,
                    "user_count": user_count,
                    "coverage_percentage": round(coverage, 1)
                })
                
        # Sort by role count (descending) and then by coverage (ascending)
        skill_gaps.sort(key=lambda x: (-x["role_count"], x["coverage_percentage"]))
                
        # Get recent assessment activity
        recent_assessments = db.query(
            models.AssessmentResult.id,
            UserModel.username,
            Assessment.title,
            models.AssessmentResult.score,
            models.AssessmentResult.completed_at
        ).join(
            UserModel, models.AssessmentResult.user_id == UserModel.id
        ).join(
            Assessment, models.AssessmentResult.assessment_id == Assessment.id
        ).order_by(
            models.AssessmentResult.completed_at.desc()
        ).limit(5).all()
        
        assessment_activity = []
        for id, username, title, score, completed_at in recent_assessments:
            assessment_activity.append({
                "id": id,
                "username": username,
                "assessment_title": title,
                "score": score,
                "completed_at": completed_at
            })
        
        # Combine data for organization dashboard
        dashboard_data = {
            "user_count": total_users,
            "department_distribution": dept_counts,
            "skill_category_distribution": skill_counts,
            "top_skills": top_skills,
            "critical_skill_gaps": skill_gaps[:5],  # Top 5 critical gaps
            "recent_assessment_activity": assessment_activity,
            "generated_at": datetime.now().isoformat()
        }
        
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating organization dashboard: {str(e)}")