from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth
from moderation import moderate_content
from websocket_manager import manager

router = APIRouter(prefix="/comments", tags=["Comments"])


def serialize_comment(comment: models.Comment) -> dict:
    return {
        "id": comment.id,
        "post_id": comment.post_id,
        "author_username": comment.author.username if comment.author else "Anonymous",
        "body": comment.body,
        "created_at": comment.created_at.isoformat(),
    }


@router.get("/{post_id}", response_model=List[dict])
def get_comments(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    comments = (
        db.query(models.Comment)
        .filter(models.Comment.post_id == post_id, models.Comment.is_removed == False)
        .order_by(models.Comment.created_at.asc())
        .all()
    )
    return [serialize_comment(c) for c in comments]


@router.post("/{post_id}", response_model=dict)
async def add_comment(
    post_id: int,
    data: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(auth.get_current_user)
):
    post = db.query(models.Post).filter(models.Post.id == post_id, models.Post.is_removed == False).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    check = moderate_content(data.body)
    if not check["allowed"]:
        raise HTTPException(status_code=400, detail=f"Comment flagged: {check['issues']}")

    comment = models.Comment(
        post_id=post_id,
        author_id=current_user.id if current_user else None,
        body=check["clean_text"],
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    serialized = serialize_comment(comment)
    await manager.broadcast_new_comment(serialized)
    return serialized


@router.delete("/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_user)
):
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    comment.is_removed = True
    db.commit()
    return {"message": "Comment removed"}
