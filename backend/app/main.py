from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import time

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.routers import auth, users, resumes, jobs, swipes, applications, analytics, recruiter, admin, ai_tools
from app.seed import seed_database

# Create tables
Base.metadata.create_all(bind=engine)

# Auto seed database on startup
try:
    seed_database()
except Exception as e:
    print(f"Startup seed notice: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SwipeX – AI Swipe-Based Intelligent Job Discovery & Career Assistance Platform API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# rate limit in-memory cache
rate_limit_cache = {}

@app.middleware("http")
async def add_security_and_telemetry_headers(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    # Rate Limit API calls (Max 100 requests per minute)
    path = request.url.path
    if path.startswith("/api/v1"):
        ip_cache = rate_limit_cache.get(client_ip, [])
        # filter requests in last 60 seconds
        ip_cache = [t for t in ip_cache if now - t < 60]
        if len(ip_cache) > 100:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=429, content={"detail": "Too many requests. Please slow down."})
        ip_cache.append(now)
        rate_limit_cache[client_ip] = ip_cache

    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000

    # Log telemetry for API calls
    if path.startswith("/api/v1"):
        category = "API"
        if "/ai" in path:
            category = "AI"
        elif "/auth" in path:
            category = "Auth"
            
        db = SessionLocal()
        try:
            from app.models import TelemetryLog
            telemetry = TelemetryLog(
                endpoint=path,
                status_code=response.status_code,
                response_time_ms=duration_ms,
                category=category
            )
            db.add(telemetry)
            db.commit()
        except Exception as e:
            print(f"Telemetry logging error: {e}")
        finally:
            db.close()

    # Apply security headers
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com https://cdn.tailwindcss.com; img-src 'self' data: https://fastapi.tiangolo.com https://images.unsplash.com; font-src 'self' https://fonts.gstatic.com;"
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include API routers under /api/v1
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(resumes.router, prefix=settings.API_V1_STR)
app.include_router(jobs.router, prefix=settings.API_V1_STR)
app.include_router(swipes.router, prefix=settings.API_V1_STR)
app.include_router(applications.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(recruiter.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(ai_tools.router, prefix=settings.API_V1_STR)

@app.post(f"{settings.API_V1_STR}/seed")
def seed_endpoint():
    seed_database()
    return {"message": "Database successfully re-seeded with sample dataset."}

# Mount static directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Serve main single-page application at root /
@app.get("/")
def read_root():
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "message": "Welcome to SwipeX AI Platform API",
        "docs": "/docs",
        "version": settings.VERSION
    }
