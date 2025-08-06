from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from datetime import datetime

from app.extraction.pipeline import run_extraction_pipeline
from app.database import get_supabase_client
app = FastAPI(
    title="Recipe Extractor API",
    description="Backend service for processing and storing recipes from various sources",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

@app.get("/")
async def root():
    return {"message": "Recipe Extractor API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/extract")
async def extract(link: str):
    try:
        return run_extraction_pipeline(link)
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 