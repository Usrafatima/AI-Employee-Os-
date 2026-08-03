from fastapi import APIRouter
router = APIRouter()
@router.get("/")
def get_workflows_status():
    return {"module": "Workflows", "status": "active"}
