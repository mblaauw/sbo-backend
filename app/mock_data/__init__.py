"""
Package containing mock data generation for the SBO application.
"""

from .mock_data import (
    get_mock_skills_taxonomy,
    get_mock_users, 
    get_mock_job_roles, 
    get_mock_assessments,
    generate_assessment_results,
    generate_llm_assessment_questions,
    analyze_resume,
    generate_learning_path,
    extract_skills_from_text,
    map_skills_to_taxonomy
)