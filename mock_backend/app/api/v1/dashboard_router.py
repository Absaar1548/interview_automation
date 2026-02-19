from fastapi import APIRouter, Depends
from typing import Dict

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats() -> Dict[str, int]:
    """
    Get dashboard statistics.
    For now, returning static mock data.
    """
    return {
        "total_interviews": 24,
        "completed": 15,
        "pending": 7,
        "flagged": 2
    }
