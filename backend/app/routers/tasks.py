from fastapi import APIRouter
router = APIRouter()
@router.get("/")
def get_tasks_status():
    return {"module": "Tasks", "status": "active"}
