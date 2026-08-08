from fastapi import APIRouter
router = APIRouter()
@router.get("/")
def get_users_status():
    return {"module": "Users", "status": "active"}
