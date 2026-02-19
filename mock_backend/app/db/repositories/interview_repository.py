"""
Interview Repository
---------------------
Handles all MongoDB CRUD operations on the `interviews` collection.
"""

from datetime import datetime
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class InterviewRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.get_collection("interviews")

    # ─── Query helpers ────────────────────────────────────────────────────────

    async def get_by_id(self, interview_id: str) -> Optional[dict]:
        """Fetch a single interview by its ObjectId string."""
        try:
            oid = ObjectId(interview_id)
        except Exception:
            return None
        doc = await self.collection.find_one({"_id": oid})
        return doc

    async def get_active_interview_for_candidate(self, candidate_id: str) -> Optional[dict]:
        """
        Returns the first interview for this candidate whose status is
        'scheduled' or 'in_progress', or None if no such document exists.
        This enforces the one-active-interview-per-candidate rule.
        """
        try:
            cid = ObjectId(candidate_id)
        except Exception:
            return None
        doc = await self.collection.find_one(
            {
                "candidate_id": str(cid),
                "status": {"$in": ["scheduled", "in_progress"]},
            }
        )
        return doc

    # ─── Writes ───────────────────────────────────────────────────────────────

    async def create_interview(self, interview_doc: dict) -> dict:
        """
        Insert a new interview document and return it with the generated _id
        represented as the string key 'id'.
        """
        result = await self.collection.insert_one(interview_doc)
        interview_doc["id"] = str(result.inserted_id)
        return interview_doc

    async def update_scheduled_at(
        self, interview_id: str, scheduled_at: datetime
    ) -> bool:
        """
        Update the scheduled_at field. Returns True when a document was modified.
        """
        now = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": ObjectId(interview_id)},
            {"$set": {"scheduled_at": scheduled_at, "updated_at": now}},
        )
        return result.modified_count == 1

    async def cancel_interview(
        self, interview_id: str, reason: Optional[str] = None
    ) -> bool:
        """
        Set status to 'cancelled'. Document is never deleted.
        Returns True when a document was modified.
        """
        now = datetime.utcnow()
        update_fields: dict = {
            "status": "cancelled",
            "cancelled_at": now,
            "updated_at": now,
        }
        if reason is not None:
            update_fields["cancellation_reason"] = reason

        result = await self.collection.update_one(
            {"_id": ObjectId(interview_id)},
            {"$set": update_fields},
        )
        return result.modified_count == 1

    # ─── Admin summary ────────────────────────────────────────────────────────

    async def get_all_summary(self) -> list:
        """
        Returns a lightweight list of all interviews — one per interview doc.
        Projection excludes curated_questions for performance.
        """
        projection = {
            "_id": 1,
            "candidate_id": 1,
            "status": 1,
            "scheduled_at": 1,
        }
        cursor = self.collection.find({}, projection)
        results = []
        async for doc in cursor:
            results.append({
                "interview_id": str(doc["_id"]),
                "candidate_id": doc.get("candidate_id"),
                "status": doc.get("status"),
                "scheduled_at": doc.get("scheduled_at"),
            })
        return results

    # ─── Candidate active/in-progress lookup ──────────────────────────────────

    async def get_active_or_inprogress_for_candidate(self, candidate_id: str) -> Optional[dict]:
        """
        Returns the first interview for this candidate whose status is
        'scheduled' or 'in_progress'. Used by the candidate /active endpoint.
        """
        doc = await self.collection.find_one(
            {
                "candidate_id": candidate_id,
                "status": {"$in": ["scheduled", "in_progress"]},
            }
        )
        return doc

    # ─── Start interview → create session ────────────────────────────────────

    async def start_interview(
        self, interview_id: str, candidate_id: str
    ) -> dict:
        """
        Idempotent: if an active session already exists for this interview,
        return its id. Otherwise insert a new session doc and flip the
        interview status to 'in_progress'.

        Returns a dict with keys: session_id, interview_id.
        """
        sessions = self.collection.database.get_collection("interview_sessions")
        now = datetime.utcnow()

        # Check for an existing active session
        existing = await sessions.find_one(
            {"interview_id": interview_id, "status": "active"}
        )
        if existing:
            return {
                "session_id": str(existing["_id"]),
                "interview_id": interview_id,
            }

        # Create a new session
        session_doc = {
            "interview_id": interview_id,
            "candidate_id": candidate_id,
            "started_at": now,
            "status": "active",
        }
        result = await sessions.insert_one(session_doc)
        session_id = str(result.inserted_id)

        # Transition interview to in_progress
        await self.collection.update_one(
            {"_id": ObjectId(interview_id)},
            {"$set": {"status": "in_progress", "started_at": now, "updated_at": now}},
        )

        return {
            "session_id": session_id,
            "interview_id": interview_id,
        }
