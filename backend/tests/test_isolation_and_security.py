import pytest
import random
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def create_random_user(role="user"):
    rand_id = random.randint(100000, 999999)
    email = f"user_{rand_id}@swipex-security.io"
    password = "Password123!"
    full_name = f"Security Tester {rand_id}"
    
    reg_res = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "fullName": full_name,
        "role": role
    })
    assert reg_res.status_code == 200
    data = reg_res.json()
    return data["access_token"], data["user"]

def test_registration_onboarding_and_no_demo_data():
    """Verify that a newly registered user gets a clean, empty state with no demo data."""
    token, user = create_random_user()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Verify profile is initialized but empty
    profile_res = client.get("/api/v1/users/profile", headers=headers)
    assert profile_res.status_code == 200
    profile_data = profile_res.json()
    assert profile_data["headline"] is None
    assert profile_data["bio"] is None
    assert profile_data["skills"] == []

    # Verify no resumes exist
    resumes_res = client.get("/api/v1/resumes/", headers=headers)
    assert resumes_res.status_code == 200
    assert resumes_res.json() == []

    # Verify no applications exist
    apps_res = client.get("/api/v1/applications/", headers=headers)
    assert apps_res.status_code == 200
    assert apps_res.json() == []

    # Verify dashboard analytics summaries are 0
    analytics_res = client.get("/api/v1/analytics/dashboard", headers=headers)
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert analytics_data["summary"]["total_applied"] == 0
    assert analytics_data["summary"]["saved_jobs"] == 0
    assert analytics_data["summary"]["shortlisted"] == 0
    assert analytics_data["summary"]["latest_ats_score"] == 0
    assert analytics_data["skill_gap_report"]["top_missing_skills"] == []

def test_multitenant_cross_user_isolation():
    """Verify that User A cannot read or access User B's resumes or private files."""
    # 1. Register User A and upload a dummy text resume
    token_a, user_a = create_random_user()
    headers_a = {"Authorization": f"Bearer {token_a}"}
    
    import io
    dummy_file = io.BytesIO(b"Candidate Skills: Python, Docker, FastAPI. Experience: 4 years.")
    dummy_file.name = "my_resume.txt"
    
    upload_res = client.post(
        "/api/v1/resumes/upload",
        headers=headers_a,
        files={"file": (dummy_file.name, dummy_file, "text/plain")}
    )
    assert upload_res.status_code == 200
    resume_a_data = upload_res.json()
    file_path = resume_a_data["file_path"] # e.g. uploads/{user_id}/filename.txt

    # 2. Register User B
    token_b, user_b = create_random_user()
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User B tries to download User A's resume file directly from the uploads route
    # The route is served as /uploads/{user_id}/{filename}
    parts = file_path.split("/")
    filename = parts[-1]
    
    exploit_url = f"/uploads/{user_a['id']}/{filename}"
    forbidden_res = client.get(exploit_url, headers=headers_b)
    # Must reject with 403 Forbidden
    assert forbidden_res.status_code == 403
    
    # 4. User B tries to view resumes list, must only see their own empty list
    resumes_b_res = client.get("/api/v1/resumes/", headers=headers_b)
    assert resumes_b_res.status_code == 200
    assert resumes_b_res.json() == []

def test_jobs_endpoint_requires_jwt():
    """Verify that job endpoints enforce JWT verification and reject anonymous calls."""
    res1 = client.get("/api/v1/jobs/")
    assert res1.status_code == 401
    
    res2 = client.get("/api/v1/jobs/1")
    assert res2.status_code == 401

def test_admin_dashboard_permissions():
    """Verify that regular users cannot call administrative endpoints."""
    token, user = create_random_user()
    headers = {"Authorization": f"Bearer {token}"}

    res_users = client.get("/api/v1/admin/users", headers=headers)
    assert res_users.status_code == 403

    res_stats = client.get("/api/v1/admin/stats", headers=headers)
    assert res_stats.status_code == 403

def test_google_login_invalid_token():
    """Verify that the google login route rejects invalid or expired Google ID tokens."""
    response = client.post("/api/v1/auth/google", json={
        "email": "invalid-email@swipex.io",
        "fullName": "Invalid Google User",
        "googleToken": "invalid_fake_token_12345",
        "role": "user"
    })
    # Since the token is invalid, it must reject with 400
    assert response.status_code == 400
    assert "google token verification failed" in response.json()["detail"].lower() or "invalid google token" in response.json()["detail"].lower()
