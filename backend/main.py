from fastapi import FastAPI
from backend.api.v1.endpoints import (
    session_router,
    question_router,
    submit_evaluation_router,
    code_ide_router,
    conversation_router,
    proctoring_router,
    summary_router,
    custom_question_router,
    zwayam_router,
    auth_router
)
from backend.database.connection import connect_to_mongo, close_mongo_connection

app = FastAPI(title="AI Interview Automation Backend")

# Initialize MongoDB connection on startup
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

# Close MongoDB connection on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

# Router inclusions
app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(session_router.router, prefix="/api/v1/session", tags=["Session"])
app.include_router(question_router.router, prefix="/api/v1/question", tags=["Question"])
app.include_router(submit_evaluation_router.router, prefix="/api/v1/submit", tags=["Submit"])
app.include_router(code_ide_router.router, prefix="/api/v1/code", tags=["Code"])
app.include_router(conversation_router.router, prefix="/api/v1/conversation", tags=["Conversation"])
app.include_router(proctoring_router.router, prefix="/api/v1/proctoring", tags=["Proctoring"])
app.include_router(summary_router.router, prefix="/api/v1/summary", tags=["Summary"])
app.include_router(custom_question_router.router, prefix="/api/v1/custom", tags=["Custom"])
app.include_router(zwayam_router.router, prefix="/api/v1/zwayam", tags=["Zwayam"])

@app.get("/")
async def root():
    return {"message": "AI Interview Automation Backend is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}