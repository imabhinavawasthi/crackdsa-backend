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

from app.routes.roadmap_routes import router as roadmap_router
from app.routes.auth_routes import router as auth_router
from app.routes.test_routes.auth import router as test_auth_router
from app.routes.test_routes.rbac import router as test_rbac_router
app.include_router(roadmap_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
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
