"""
Candidate Profile Router — face and voice enrollment for verification.
---------------------------------------------------------------------
Used on candidate dashboard to capture live photo and voice for later
face/audio verification during the interview (Azure Face API + Azure Speech Service).
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.v1.auth_router import get_current_active_user
from app.db.database import get_database
from app.db.models.user import UserInDB
from app.services.face_service import face_service
from app.services.speech_service import speech_service

router = APIRouter()
COLLECTION_NAME = "candidate_biometrics"


async def get_current_candidate(current_user: UserInDB = Depends(get_current_active_user)) -> UserInDB:
    if current_user.role != "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only candidates can access this endpoint",
        )
    return current_user


@router.post(
    "/profile/face",
    summary="Upload live photo for face verification",
    description="Candidate uploads a live camera photo. Stored for face verification during interview (Azure Face API–ready).",
)
async def upload_face(
    current_candidate: UserInDB = Depends(get_current_candidate),
    db: AsyncIOMotorDatabase = Depends(get_database),
    photo: UploadFile = File(..., description="Live photo (image/jpeg or image/png)"),
):
    candidate_id = str(current_candidate.id)
    content_type = photo.content_type or "image/jpeg"
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image (e.g. image/jpeg, image/png)",
        )
    image_bytes = await photo.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty image")
    ref_id, path_or_azure_id = face_service.enroll_face(candidate_id, image_bytes, content_type)
    coll = db[COLLECTION_NAME]
    await coll.update_one(
        {"candidate_id": candidate_id},
        {
            "$set": {
                "face_ref_id": ref_id,
                "face_path_or_azure_id": path_or_azure_id,
                "face_updated_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        },
        upsert=True,
    )
    return {
        "message": "Face enrolled successfully. It will be used for verification during the interview.",
        "face_ref_id": ref_id,
    }


@router.post(
    "/profile/voice",
    summary="Upload live voice recording for audio verification",
    description="Candidate uploads a short voice recording. Stored for voice verification during interview (Azure Speech Service–ready).",
)
async def upload_voice(
    current_candidate: UserInDB = Depends(get_current_candidate),
    db: AsyncIOMotorDatabase = Depends(get_database),
    audio: UploadFile = File(..., description="Voice recording (audio/webm, audio/wav, etc.)"),
):
    candidate_id = str(current_candidate.id)
    content_type = audio.content_type or "audio/webm"
    if not content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an audio recording (e.g. audio/webm, audio/wav)",
        )
    audio_bytes = await audio.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty audio")
    ref_id, path_or_azure_id = speech_service.enroll_voice(candidate_id, audio_bytes, content_type)
    coll = db[COLLECTION_NAME]
    await coll.update_one(
        {"candidate_id": candidate_id},
        {
            "$set": {
                "voice_ref_id": ref_id,
                "voice_path_or_azure_id": path_or_azure_id,
                "voice_updated_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        },
        upsert=True,
    )
    return {
        "message": "Voice enrolled successfully. It will be used for verification during the interview.",
        "voice_ref_id": ref_id,
    }


@router.get(
    "/profile/verification-status",
    summary="Get face and voice enrollment status",
    description="Returns whether the candidate has enrolled face and voice for interview verification.",
)
async def get_verification_status(
    current_candidate: UserInDB = Depends(get_current_candidate),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    candidate_id = str(current_candidate.id)
    coll = db[COLLECTION_NAME]
    doc = await coll.find_one({"candidate_id": candidate_id})
    return {
        "face_enrolled": bool(doc and doc.get("face_ref_id")),
        "voice_enrolled": bool(doc and doc.get("voice_ref_id")),
        "face_updated_at": doc.get("face_updated_at").isoformat() if doc and doc.get("face_updated_at") else None,
        "voice_updated_at": doc.get("voice_updated_at").isoformat() if doc and doc.get("voice_updated_at") else None,
    }
