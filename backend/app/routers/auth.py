from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_status():
    return {"module": "Authentication", "status": "active"}
