import json
import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.models.document import Document, DocumentQA, DocumentStatus, DocumentType
from app.schemas.document import DocumentOut, DocumentQARequest, DocumentQAOut
from app.services import ocr_service, productivity_ai_service as ai_service

router = APIRouter(tags=["Document Intelligence"])


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    company_id: uuid.UUID = Form(...),
    document_type: DocumentType = Form(DocumentType.other),
    uploaded_by: uuid.UUID | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_ext = file.filename.split(".")[-1].lower()
    saved_name = f"{uuid.uuid4()}.{file_ext}"
    saved_path = os.path.join(settings.UPLOAD_DIR, saved_name)

    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(413, f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    with open(saved_path, "wb") as f:
        f.write(contents)

    document = Document(
        company_id=company_id,
        uploaded_by=uploaded_by,
        file_name=file.filename,
        file_path=saved_path,
        file_type=file_ext,
        document_type=document_type,
        status=DocumentStatus.uploaded,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.post("/{document_id}/process", response_model=DocumentOut)
def process_document(document_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Runs OCR/text extraction + AI summarization + entity extraction.
    Kept as a separate step (rather than automatic on upload) so large files
    can be processed via a background worker/queue in production.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")

    document.status = DocumentStatus.processing
    db.commit()

    try:
        extracted_text = ocr_service.extract_text(document.file_path, document.file_type)
        ai_result = ai_service.summarize_document(extracted_text, document.document_type.value)

        document.extracted_text = extracted_text
        document.ai_summary = ai_result.get("summary", "")
        document.key_entities = json.dumps(ai_result.get("key_entities", {}))
        document.status = DocumentStatus.processed
    except Exception as e:
        document.status = DocumentStatus.failed
        document.ai_summary = f"Processing failed: {str(e)}"

    db.commit()
    db.refresh(document)
    return document


@router.get("", response_model=List[DocumentOut])
def list_documents(company_id: uuid.UUID, db: Session = Depends(get_db)):
    return (
        db.query(Document)
        .filter(Document.company_id == company_id)
        .order_by(Document.created_at.desc())
        .all()
    )


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: uuid.UUID, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")
    return document


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: uuid.UUID, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    db.delete(document)
    db.commit()


@router.post("/{document_id}/ask", response_model=DocumentQAOut, status_code=201)
def ask_document(document_id: uuid.UUID, payload: DocumentQARequest, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")
    if not document.extracted_text:
        raise HTTPException(400, "Document has not been processed yet. Call /process first.")

    answer = ai_service.answer_document_question(document.extracted_text, payload.question)

    qa = DocumentQA(
        document_id=document_id,
        question=payload.question,
        answer=answer,
        asked_by=payload.asked_by,
    )
    db.add(qa)
    db.commit()
    db.refresh(qa)
    return qa


@router.get("/{document_id}/qa-history", response_model=List[DocumentQAOut])
def qa_history(document_id: uuid.UUID, db: Session = Depends(get_db)):
    return (
        db.query(DocumentQA)
        .filter(DocumentQA.document_id == document_id)
        .order_by(DocumentQA.created_at.desc())
        .all()
    )