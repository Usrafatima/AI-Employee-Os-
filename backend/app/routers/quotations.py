from fastapi import APIRouter
router = APIRouter()
@router.get("/")
def get_quotations_status():
    return {"module": "Quotations", "status": "active"}
