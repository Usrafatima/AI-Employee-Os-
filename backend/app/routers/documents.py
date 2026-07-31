from fastapi import APIRouter
router = APIRouter()
@router.get("/")
def get_documents_status():
    return {"module": "Documents", "status": "active"}
