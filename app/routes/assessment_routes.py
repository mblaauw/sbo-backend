"""
Assessment service endpoints for SBO application.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from database import get_db, get_db_context
from middleware import get_current_user, User
from models import (
    Assessment, AssessmentQuestion, AssessmentResult, Skill, UserSkill
)
import schemas
from mock_data import generate_llm_assessment_questions

logger = logging.getLogger("sbo.assessment_routes")

router = APIRouter(tags=["assessments"])

@router.get("/assessments", response_model=List[schemas.Assessment])
def get_all_assessments(
    skill_id: Optional[int] = None,
    difficulty: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all assessments with optional filtering"""
    query = db.query(Assessment)

    if skill_id:
        query = query.filter(Assessment.skill_id == skill_id)
    if difficulty:
        query = query.filter(Assessment.difficulty_level == difficulty)

    assessments = query.offset(skip).limit(limit).all()
    return assessments

@router.get("/assessments/{assessment_id}", response_model=schemas.AssessmentDetail)
def get_assessment(
    assessment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific assessment by ID"""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Get questions for this assessment
    questions = db.query(AssessmentQuestion).filter(
        AssessmentQuestion.assessment_id == assessment_id
    ).all()

    return schemas.AssessmentDetail(
        id=assessment.id,
        title=assessment.title,
        description=assessment.description,
        skill_id=assessment.skill_id,
        difficulty_level=assessment.difficulty_level,
        questions=[
            schemas.AssessmentQuestionDetail(
                id=q.id,
                question_text=q.question_text,
                options=q.options,
                correct_answer_index=q.correct_answer_index,
                explanation=q.explanation
            ) for q in questions
        ]
    )

@router.post("/assessments", response_model=schemas.Assessment)
def create_assessment(
    assessment_create: schemas.AssessmentCreate,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new assessment"""
    try:
        # Check if skill exists
        skill = db.query(Skill).filter(Skill.id == assessment_create.skill_id).first()
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")

        # Create assessment
        db_assessment = Assessment(
            title=assessment_create.title,
            description=assessment_create.description,
            skill_id=assessment_create.skill_id,
            difficulty_level=assessment_create.difficulty_level
        )
        db.add(db_assessment)
        db.commit()
        db.refresh(db_assessment)

        # Generate questions in the background if not provided
        if not assessment_create.questions:
            background_tasks.add_task(
                generate_and_add_questions,
                assessment_id=db_assessment.id,
                skill_name=skill.name,
                difficulty_level=assessment_create.difficulty_level
            )
        else:
            # Add provided questions
            for question in assessment_create.questions:
                db_question = AssessmentQuestion(
                    assessment_id=db_assessment.id,
                    question_text=question.question_text,
                    options=question.options,
                    correct_answer_index=question.correct_answer_index,
                    explanation=question.explanation
                )
                db.add(db_question)
            db.commit()

        return db_assessment
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating assessment: {str(e)}")

@router.get("/users/{user_id}/assessment-results", response_model=List[schemas.AssessmentResultSummary])
def get_user_assessment_results(
    user_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get assessment results for a user"""
    try:
        results = db.query(AssessmentResult).filter(
            AssessmentResult.user_id == user_id
        ).all()

        # Get assessment details for each result
        result_summaries = []
        for result in results:
            assessment = db.query(Assessment).filter(
                Assessment.id == result.assessment_id
            ).first()

            if assessment:
                result_summaries.append(
                    schemas.AssessmentResultSummary(
                        id=result.id,
                        assessment_id=result.assessment_id,
                        assessment_title=assessment.title,
                        skill_id=assessment.skill_id,
                        score=result.score,
                        proficiency_level=result.proficiency_level,
                        completed_at=result.completed_at
                    )
                )

        return result_summaries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving assessment results: {str(e)}")

@router.post("/assessments/{assessment_id}/submit", response_model=schemas.AssessmentResult)
def submit_assessment(
    assessment_id: int,
    submission: schemas.AssessmentSubmission,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit assessment answers and get results"""
    try:
        # Check if assessment exists
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        # Get questions for this assessment
        questions = db.query(AssessmentQuestion).filter(
            AssessmentQuestion.assessment_id == assessment_id
        ).all()

        if len(questions) == 0:
            raise HTTPException(status_code=400, detail="Assessment has no questions")

        # Create a map of question IDs to correct answers
        correct_answers = {q.id: q.correct_answer_index for q in questions}

        # Calculate score
        num_correct = 0
        question_results = []

        for answer in submission.answers:
            if answer.question_id not in correct_answers:
                raise HTTPException(status_code=400, detail=f"Question ID {answer.question_id} not found in assessment")

            is_correct = answer.selected_option_index == correct_answers[answer.question_id]

            if is_correct:
                num_correct += 1

            question_results.append(
                schemas.QuestionResult(
                    question_id=answer.question_id,
                    is_correct=is_correct,
                    correct_answer_index=correct_answers[answer.question_id]
                )
            )

        # Calculate percentage score
        percentage_score = (num_correct / len(questions)) * 100 if questions else 0

        # Determine proficiency level based on score
        proficiency_level = 1  # Default to lowest level
        if percentage_score >= 90:
            proficiency_level = 5
        elif percentage_score >= 80:
            proficiency_level = 4
        elif percentage_score >= 70:
            proficiency_level = 3
        elif percentage_score >= 60:
            proficiency_level = 2

        # Save assessment result
        db_result = AssessmentResult(
            assessment_id=assessment_id,
            user_id=submission.user_id,
            score=percentage_score,
            proficiency_level=proficiency_level,
            completed_at=datetime.now()
        )
        db.add(db_result)

        # Update user's skill level if this is a skill assessment
        if assessment.skill_id:
            user_skill = db.query(UserSkill).filter(
                UserSkill.user_id == submission.user_id,
                UserSkill.skill_id == assessment.skill_id
            ).first()

            if user_skill:
                # Update only if assessment shows higher proficiency
                if proficiency_level > user_skill.proficiency_level:
                    user_skill.proficiency_level = proficiency_level
                    user_skill.is_verified = True
                    user_skill.source = "assessment"
                    user_skill.last_verified = datetime.now()
            else:
                # Add new skill
                new_skill = UserSkill(
                    user_id=submission.user_id,
                    skill_id=assessment.skill_id,
                    proficiency_level=proficiency_level,
                    is_verified=True,
                    source="assessment",
                    last_verified=datetime.now()
                )
                db.add(new_skill)

        db.commit()
        db.refresh(db_result)

        return schemas.AssessmentResult(
            id=db_result.id,
            assessment_id=assessment_id,
            user_id=submission.user_id,
            score=percentage_score,
            proficiency_level=proficiency_level,
            question_results=question_results,
            completed_at=db_result.completed_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error submitting assessment: {str(e)}")

def generate_and_add_questions(assessment_id: int, skill_name: str, difficulty_level: str, num_questions: int = 5):
    """Background task to generate and add questions for an assessment"""
    with get_db_context() as db:
        try:
            # Generate questions
            questions_data = generate_llm_assessment_questions(skill_name, num_questions)

            # Add questions to the database
            for question in questions_data["questions"]:
                db_question = AssessmentQuestion(
                    assessment_id=assessment_id,
                    question_text=question["question"],
                    options=question["options"],
                    correct_answer_index=question["correct_answer_index"],
                    explanation=question["explanation"]
                )
                db.add(db_question)

            db.commit()
            logger.info(f"Added {len(questions_data['questions'])} questions to assessment {assessment_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error generating questions: {str(e)}")
            # Add default questions as fallback
            default_questions = [
                {
                    "question_text": f"Sample question 1 for {skill_name}",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer_index": 0,
                    "explanation": "This is a sample explanation for the correct answer."
                },
                {
                    "question_text": f"Sample question 2 for {skill_name}",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer_index": 1,
                    "explanation": "This is a sample explanation for the correct answer."
                }
            ]

            try:
                for question in default_questions:
                    db_question = AssessmentQuestion(
                        assessment_id=assessment_id,
                        question_text=question["question_text"],
                        options=question["options"],
                        correct_answer_index=question["correct_answer_index"],
                        explanation=question["explanation"]
                    )
                    db.add(db_question)

                db.commit()
                logger.info(f"Added default questions for assessment {assessment_id} due to error")
            except Exception as inner_e:
                db.rollback()
                logger.error(f"Error adding default questions: {str(inner_e)}")
