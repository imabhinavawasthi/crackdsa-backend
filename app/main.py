from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_supabase_client, check_database_connection
from datetime import datetime
import logging

# Set up simple logging to see what starts
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CrackDSA API",
    description="Backend API for the CrackDSA coding interview preparation platform",
    version="0.1.0",
)

import os

# Add CORS middleware for OAuth flow
# In production, restrict origins to deployed frontend URL
allowed_origins = [
    "http://localhost:3000", 
    "http://localhost:3001", 
    "http://127.0.0.1:3000"
]

# Add specific FRONTEND_URL if defined in environment
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    # This regex natively allows deployed Vercel/Render frontend URLs to access the API 
    # while maintaining 'allow_credentials=True'. 
    allow_origin_regex=r"https://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routes.roadmap_routes import router as roadmap_router, admin_router as roadmap_admin_router
from app.routes.auth_routes import router as auth_router
from app.routes.dsa_sheet_routes import public_router, admin_router
from app.routes.course_routes import public_router as course_public_router, admin_router as course_admin_router
from app.routes.instructor_routes import public_router as instructor_public_router, admin_router as instructor_admin_router
from app.routes.video_lecture_routes import public_router as video_public_router, admin_router as video_admin_router
from app.routes.practice_problem_routes import public_router as problem_public_router, admin_router as problem_admin_router
from app.routes.article_routes import public_router as article_public_router, admin_router as article_admin_router
from app.routes.user_asset_state_routes import router as user_asset_state_router
from app.routes.checkout_routes import router as checkout_router
from app.routes.admin_payments_routes import router as admin_payments_router
from app.routes.test_routes.auth import router as test_auth_router
from app.routes.test_routes.rbac import router as test_rbac_router
app.include_router(roadmap_router, prefix="/api/v1")
app.include_router(roadmap_admin_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(public_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(course_public_router, prefix="/api/v1")
app.include_router(course_admin_router, prefix="/api/v1")
app.include_router(instructor_public_router, prefix="/api/v1")
app.include_router(instructor_admin_router, prefix="/api/v1")
app.include_router(video_public_router, prefix="/api/v1")
app.include_router(video_admin_router, prefix="/api/v1")
app.include_router(problem_public_router, prefix="/api/v1")
app.include_router(problem_admin_router, prefix="/api/v1")
app.include_router(article_public_router, prefix="/api/v1")
app.include_router(article_admin_router, prefix="/api/v1")
app.include_router(user_asset_state_router, prefix="/api/v1")
app.include_router(checkout_router, prefix="/api/v1")
app.include_router(admin_payments_router, prefix="/api/v1")
app.include_router(test_auth_router)
app.include_router(test_rbac_router)

@app.on_event("startup")
def on_startup():
    """Startup event to verify Supabase connection and log initialization."""
    logger.info("FastAPI service starting...")
    
    try:
        # Initialize Supabase client
        client = get_supabase_client()
        logger.info("Supabase client initialized successfully")
        
        # Verify database connection
        if check_database_connection():
            logger.info("Database connection verified - service ready")
        else:
            logger.warning("Database connection check failed - service may not be fully operational")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise

@app.get("/")
def read_root():
    return {"message": "CrackDSA API running"}

@app.get("/health")
def health_check(response: Response):
    """
    Health check endpoint that reports app status and database connectivity.
    
    Returns:
        dict: Health status with app status, database status, and timestamp
        Status Code: 200 if everything is healthy, 503 if database is unreachable
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    try:
        # Check database connection
        db_connected = check_database_connection()
        
        if db_connected:
            response.status_code = 200
            return {
                "status": "ok",
                "database": "connected",
                "timestamp": timestamp
            }
        else:
            response.status_code = 503
            return {
                "status": "degraded",
                "database": "disconnected",
                "timestamp": timestamp
            }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        response.status_code = 503
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e),
            "timestamp": timestamp
        }
