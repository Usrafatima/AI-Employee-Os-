import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.knowledge import KnowledgeArticle
from app.schemas.knowledge import KnowledgeArticleCreate, KnowledgeArticleOut, KnowledgeSearchRequest
from app.services import ai_service

router = APIRouter(tags=["Knowledge Base"])


@router.post("", response_model=KnowledgeArticleOut, status_code=201)
def create_article(payload: KnowledgeArticleCreate, db: Session = Depends(get_db)):
    article = KnowledgeArticle(**payload.model_dump(), source_type="manual")
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.get("", response_model=List[KnowledgeArticleOut])
def list_articles(company_id: uuid.UUID, db: Session = Depends(get_db)):
    return (
        db.query(KnowledgeArticle)
        .filter(KnowledgeArticle.company_id == company_id)
        .order_by(KnowledgeArticle.updated_at.desc())
        .all()
    )


@router.get("/{article_id}", response_model=KnowledgeArticleOut)
def get_article(article_id: uuid.UUID, db: Session = Depends(get_db)):
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if not article:
        raise HTTPException(404, "Article not found")
    return article


@router.delete("/{article_id}", status_code=204)
def delete_article(article_id: uuid.UUID, db: Session = Depends(get_db)):
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if not article:
        raise HTTPException(404, "Article not found")
    db.delete(article)
    db.commit()


@router.post("/search")
def search_knowledge_base(payload: KnowledgeSearchRequest, db: Session = Depends(get_db)):
    """
    Keyword-filter the company's knowledge base for candidate articles, then let the
    AI compose a direct answer citing which article(s) it used. A production version
    would swap the keyword filter for a vector-embedding similarity search.
    """
    like_pattern = f"%{payload.query}%"
    candidates = (
        db.query(KnowledgeArticle)
        .filter(
            KnowledgeArticle.company_id == payload.company_id,
            or_(
                KnowledgeArticle.title.ilike(like_pattern),
                KnowledgeArticle.content.ilike(like_pattern),
                KnowledgeArticle.tags.ilike(like_pattern),
            ),
        )
        .limit(10)
        .all()
    )

    if not candidates:
        candidates = (
            db.query(KnowledgeArticle)
            .filter(KnowledgeArticle.company_id == payload.company_id)
            .order_by(KnowledgeArticle.updated_at.desc())
            .limit(10)
            .all()
        )

    snippets = [f"{a.title}: {a.content}" for a in candidates]
    if not snippets:
        return {"answer": "No knowledge base articles found for this company yet.", "sources": []}

    answer = ai_service.answer_knowledge_query(snippets, payload.query)
    return {
        "answer": answer,
        "sources": [{"id": str(a.id), "title": a.title} for a in candidates],
    }