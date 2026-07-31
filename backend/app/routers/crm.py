from fastapi import APIRouter
router = APIRouter()
@router.get("/")
def get_crm_status():
    return {"module": "CRM", "status": "active"}
