from fastapi import APIRouter
router = APIRouter()
@router.get("/")
def get_meetings_status():
    return {"module": "Meetings", "status": "active"}
