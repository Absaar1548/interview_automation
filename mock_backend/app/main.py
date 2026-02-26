from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth_router, dashboard_router
from app.api.v1 import interview_router
from app.api.v1 import candidate_interview_router
from app.api.v1 import session_router

import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Interview Automation Mock Backend")

# CORS Middleware
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router inclusions
app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(dashboard_router.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(interview_router.router, prefix="/api/v1/admin/interviews", tags=["Interviews"])
app.include_router(candidate_interview_router.router, prefix="/api/v1/candidate/interviews", tags=["Candidate Interviews"])
app.include_router(session_router.router, prefix="/api/v1", tags=["Session"])

@app.get("/")
async def root():
    return {"message": "Mock Backend is running"}
