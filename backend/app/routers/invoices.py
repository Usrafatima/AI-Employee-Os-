from fastapi import APIRouter
router = APIRouter()
@router.get("/")
def get_invoices_status():
    return {"module": "Invoices", "status": "active"}
