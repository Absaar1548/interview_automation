from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.endpoints import (
    session_router,
    question_router,
    submit_evaluation_router,
    code_ide_router,
    conversation_router,
    proctoring_router,
    summary_router,
    custom_question_router,
    zwayam_router,
    answer_router,
    dev_router
)

app = FastAPI(title="AI Interview Automation Backend")

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
app.include_router(session_router.router, prefix="/api/v1/session", tags=["Session"])
app.include_router(question_router.router, prefix="/api/v1/question", tags=["Question"])
app.include_router(submit_evaluation_router.router, prefix="/api/v1/submit", tags=["Submit"])
app.include_router(code_ide_router.router, prefix="/api/v1/code", tags=["Code"])
app.include_router(conversation_router.router, prefix="/api/v1/conversation", tags=["Conversation"])
app.include_router(proctoring_router.router, prefix="/api/v1/proctoring", tags=["Proctoring"])
app.include_router(summary_router.router, prefix="/api/v1/summary", tags=["Summary"])
app.include_router(custom_question_router.router, prefix="/api/v1/custom", tags=["Custom"])
app.include_router(zwayam_router.router, prefix="/api/v1/zwayam", tags=["Zwayam"])
app.include_router(answer_router.router, prefix="/api/v1/answer", tags=["Answer"])
app.include_router(dev_router.router, prefix="/api/v1/dev", tags=["Dev"])

@app.get("/")
async def root():
    return {"message": "AI Interview Automation Backend is running"}
