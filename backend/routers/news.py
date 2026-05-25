"""
News router - Crypto news endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.news import News

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("")
async def get_news(limit: int = 20, db: Session = Depends(get_db)):
    """Get latest crypto news"""
    try:
        news_items = db.query(News).order_by(
            News.published_at.desc()
        ).limit(limit).all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": n.id,
                    "title": n.title,
                    "source": n.source,
                    "sentiment": n.sentiment,
                    "coins": n.coins,
                    "url": n.url,
                    "published_at": n.published_at.isoformat(),
                    "content": n.content
                }
                for n in news_items
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
