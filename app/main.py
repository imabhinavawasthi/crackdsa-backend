from fastapi import FastAPI
from app.database import engine, Base
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

# Base.metadata.create_all(bind=engine) # Keeping commented out until models exist

@app.on_event("startup")
def on_startup():
    logger.info("FastAPI service started.")

@app.get("/")
def read_root():
    return {"message": "CrackDSA API running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
