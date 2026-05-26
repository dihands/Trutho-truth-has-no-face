from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, auth

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.delete("/post/{post_id}")
def admin_delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(auth.require_admin)
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.is_removed = True
    db.commit()
    return {"message": f"Post {post_id} removed by admin"}


@router.delete("/comment/{comment_id}")
def admin_delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(auth.require_admin)
):
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment.is_removed = True
    db.commit()
    return {"message": f"Comment {comment_id} removed by admin"}


@router.post("/ban/{user_id}")
def admin_ban_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(auth.require_admin)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot ban admin")
    user.is_banned = True
    db.commit()
    return {"message": f"User {user.username} banned"}


@router.post("/unban/{user_id}")
def admin_unban_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(auth.require_admin)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_banned = False
    db.commit()
    return {"message": f"User {user.username} unbanned"}


@router.post("/verify/{post_id}")
def admin_verify_post(
    post_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(auth.require_admin)
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.verification_status = "moderator_verified"
    post.verification_score = 1.0
    db.commit()
    return {"message": f"Post {post_id} verified by moderator"}


@router.get("/stats")
def admin_stats(db: Session = Depends(get_db), admin: models.User = Depends(auth.require_admin)):
    from sqlalchemy import func
    return {
        "total_users": db.query(func.count(models.User.id)).scalar(),
        "total_posts": db.query(func.count(models.Post.id)).scalar(),
        "removed_posts": db.query(func.count(models.Post.id)).filter(models.Post.is_removed == True).scalar(),
        "banned_users": db.query(func.count(models.User.id)).filter(models.User.is_banned == True).scalar(),
        "total_comments": db.query(func.count(models.Comment.id)).scalar(),
    }
