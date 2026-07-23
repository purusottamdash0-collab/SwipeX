import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey, Enum, JSON, Index
from sqlalchemy.orm import relationship
import enum
from app.database import Base

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

class UserRole(str, enum.Enum):
    USER = "user"
    RECRUITER = "recruiter"
    RECRUITER_UNVERIFIED = "recruiter_unverified"
    ADMIN = "admin"

class SwipeType(str, enum.Enum):
    LIKE = "like"       # Swipe Right -> Apply/Interest
    SKIP = "skip"       # Swipe Left -> Pass
    SAVE = "save"       # Bookmark

class ApplicationStatus(str, enum.Enum):
    APPLIED = "Applied"
    SHORTLISTED = "Shortlisted"
    INTERVIEWING = "Interviewing"
    OFFERED = "Offered"
    REJECTED = "Rejected"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.USER.value, nullable=False, index=True)
    avatar_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    auth_provider = Column(String(50), default="email", nullable=False)
    google_id = Column(String(255), unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    swipes = relationship("SwipeAction", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    posted_jobs = relationship("Job", back_populates="recruiter", cascade="all, delete-orphan")
    coaching_logs = relationship("CoachingLog", back_populates="user", cascade="all, delete-orphan")
    mfa_credential = relationship("MfaCredential", back_populates="user", uselist=False, cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="user", foreign_keys="[Interview.user_id]", cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    headline = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    location = Column(String(100), nullable=True)
    target_role = Column(String(100), nullable=True, index=True)
    expected_salary = Column(Integer, nullable=True)
    preferred_location = Column(String(100), nullable=True)
    remote_only = Column(Boolean, default=False)
    skills = Column(JSON, default=list)
    experience_years = Column(Float, default=0.0)
    portfolio_links = Column(JSON, default=list)
    education_json = Column(JSON, default=list)
    experience_json = Column(JSON, default=list)
    projects_json = Column(JSON, default=list)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="profile")

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), default="pdf")
    parsed_text = Column(Text, nullable=True)
    extracted_skills = Column(JSON, default=list)
    ats_score = Column(Integer, default=0, index=True)
    ats_breakdown_json = Column(JSON, default=dict)
    is_primary = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="resumes")
    applications = relationship("Application", back_populates="resume")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    company_logo = Column(Text, nullable=True)
    company_type = Column(String(50), default="Startup", index=True)
    location = Column(String(255), nullable=False, index=True)
    is_remote = Column(Boolean, default=False, index=True)
    is_hybrid = Column(Boolean, default=False, index=True)
    job_type = Column(String(50), default="Full Time", index=True)
    salary_min = Column(Integer, default=0, index=True)
    salary_max = Column(Integer, default=0, index=True)
    currency = Column(String(10), default="USD")
    experience_level = Column(String(50), default="Mid Level", index=True)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, default=list)
    nice_to_have_skills = Column(JSON, default=list)
    is_fresher_friendly = Column(Boolean, default=False, index=True)
    low_competition = Column(Boolean, default=False, index=True)
    status = Column(String(50), default="active", index=True)
    applicants_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now, index=True)

    recruiter = relationship("User", back_populates="posted_jobs")
    swipes = relationship("SwipeAction", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")

class SwipeAction(Base):
    __tablename__ = "swipe_actions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="swipes")
    job = relationship("Job", back_populates="swipes")

Index("idx_user_job_swipe", SwipeAction.user_id, SwipeAction.job_id)

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True, index=True)
    match_score = Column(Float, default=0.0, index=True)
    ats_score = Column(Integer, default=0)
    status = Column(String(50), default=ApplicationStatus.APPLIED.value, index=True)
    notes = Column(Text, nullable=True)
    applied_at = Column(DateTime, default=utc_now, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")

Index("idx_user_job_application", Application.user_id, Application.job_id)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info", index=True)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="notifications")

class CoachingLog(Base):
    __tablename__ = "coaching_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(255), index=True)
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    feedback = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="coaching_logs")

class MfaCredential(Base):
    __tablename__ = "mfa_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    secret_key = Column(String(255), nullable=False)
    is_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="mfa_credential")

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action_type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="activity_logs")

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    scheduled_at = Column(DateTime, nullable=False, index=True)
    status = Column(String(50), default="Scheduled", index=True)
    interview_format = Column(String(100), default="Virtual / Zoom", index=True)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="interviews", foreign_keys=[user_id])

class TelemetryLog(Base):
    __tablename__ = "telemetry_logs"

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(255), nullable=False, index=True)
    status_code = Column(Integer, nullable=False, index=True)
    response_time_ms = Column(Float, default=0.0)
    category = Column(String(100), default="API", index=True)
    timestamp = Column(DateTime, default=utc_now, index=True)
