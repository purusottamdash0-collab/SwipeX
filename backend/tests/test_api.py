import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.ai.resume_parser import parse_resume_text
from app.ai.ats_engine import calculate_ats_score
from app.ai.matching_engine import compute_job_match

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_resume_parser_ai():
    raw_text = """
    Jane Doe
    jane@example.com | 555-0199
    Skills: Python, React, FastAPI, Docker, SQL, AWS
    Experience: Developed microservices for 4 years. Improved system performance by 40%.
    Education: BS Computer Science
    """
    parsed = parse_resume_text(raw_text)
    assert parsed["email"] == "jane@example.com"
    assert "Python" in parsed["skills"]
    assert "React" in parsed["skills"]

def test_ats_engine_scoring():
    raw_text = "John Smith\njohn@test.com\nSkills: Python, Docker, React\nExperience: Built web apps."
    parsed = parse_resume_text(raw_text)
    ats_result = calculate_ats_score(parsed)
    assert "ats_score" in ats_result
    assert 0 <= ats_result["ats_score"] <= 100

def test_job_match_calculator():
    user_profile = {"skills": ["Python", "FastAPI", "React"], "experience_years": 3.0}
    resume_data = {"parsed_text": "Experienced Python engineer with React frontend background.", "skills": ["Python", "React"]}
    job = {
        "title": "Full Stack Engineer",
        "description": "Python FastAPI and React developer needed",
        "required_skills": ["Python", "React", "FastAPI"],
        "nice_to_have_skills": ["Docker"],
        "experience_level": "Mid Level"
    }
    match_res = compute_job_match(user_profile, resume_data, job)
    assert match_res["match_percentage"] > 70.0
    assert len(match_res["missing_skills"]) == 0
