import os
import aiofiles
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
import models, schemas, auth
from websocket_manager import manager
from ranking import compute_trending_score, get_trending_posts
from moderation import moderate_content
from utils.image_cleaner import strip_exif_and_clean, is_valid_upload, ALLOWED_IMAGE_TYPES
from utils.security import secure_filename, get_upload_path
from datetime import datetime

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", 50))

router = APIRouter(prefix="/posts", tags=["Posts"])

VALID_CATEGORIES = {
    "Corruption", "Crime", "Harassment", "Road Problem",
    "Government Issue", "Scam", "Environment", "Education",
    "Healthcare", "Police Abuse", "Public Safety"
}


def serialize_post(post: models.Post, db: Session) -> dict:
    comment_count = db.query(func.count(models.Comment.id)).filter(
        models.Comment.post_id == post.id,
        models.Comment.is_removed == False
    ).scalar()
    author_name = post.author.username if post.author else "Anonymous"
    return {
        "id": post.id,
        "title": post.title,
        "body": post.body,
        "category": post.category,
        "media_url": post.media_url,
        "media_type": post.media_type,
        "author_username": author_name,
        "likes": post.likes,
        "dislikes": post.dislikes,
        "views": post.views,
        "trending_score": post.trending_score,
        "verification_status": post.verification_status,
        "created_at": post.created_at.isoformat(),
        "comment_count": comment_count,
    }


@router.get("", response_model=List[dict])
def get_posts(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    q = db.query(models.Post).filter(models.Post.is_removed == False)
    if category:
        q = q.filter(models.Post.category == category)
    if search:
        term = f"%{search}%"
        q = q.filter(
            models.Post.title.ilike(term) |
            models.Post.body.ilike(term) |
            models.Post.category.ilike(term)
        )
    posts = q.order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()
    return [serialize_post(p, db) for p in posts]


@router.get("/trending", response_model=List[dict])
def trending(limit: int = Query(20, ge=1, le=50), db: Session = Depends(get_db)):
    posts = get_trending_posts(db, limit)
    return [serialize_post(p, db) for p in posts]


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    total_posts = db.query(func.count(models.Post.id)).filter(models.Post.is_removed == False).scalar()
    total_users = db.query(func.count(models.User.id)).scalar()
    total_comments = db.query(func.count(models.Comment.id)).filter(models.Comment.is_removed == False).scalar()
    return {
        "total_posts": total_posts,
        "total_users": total_users,
        "total_comments": total_comments,
        "identities_exposed": 0
    }


@router.get("/{post_id}", response_model=dict)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id, models.Post.is_removed == False).first()
    if not post:
        raise HTTPException(status_code=404, detail="Report not found")
    post.views += 1
    post.trending_score = compute_trending_score(post)
    db.commit()
    return serialize_post(post, db)


@router.post("", response_model=dict)
async def create_post(
    title: str = Form(...),
    body: str = Form(...),
    category: str = Form(...),
    media: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(auth.get_current_user)
):
    if category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Choose from: {', '.join(VALID_CATEGORIES)}")

    # Moderate content
    title_check = moderate_content(title)
    body_check = moderate_content(body)
    if not title_check["allowed"]:
        raise HTTPException(status_code=400, detail=f"Title flagged: {title_check['issues']}")
    if not body_check["allowed"]:
        raise HTTPException(status_code=400, detail=f"Body flagged: {body_check['issues']}")

    media_url = None
    media_type = None

    if media and media.filename:
        content = await media.read()
        valid, err = is_valid_upload(media.content_type, len(content), MAX_MB)
        if not valid:
            raise HTTPException(status_code=400, detail=err)

        # Strip EXIF from images
        if media.content_type in ALLOWED_IMAGE_TYPES:
            content = strip_exif_and_clean(content, media.content_type)
            media_type = "image"
        else:
            media_type = "video"

        filename = secure_filename(media.filename)
        path = get_upload_path(UPLOAD_DIR, filename)
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        async with aiofiles.open(path, "wb") as f:
            await f.write(content)
        media_url = f"/uploads/{filename}"

    post = models.Post(
        title=title_check["clean_text"],
        body=body_check["clean_text"],
        category=category,
        media_url=media_url,
        media_type=media_type,
        author_id=current_user.id if current_user else None,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    post.trending_score = compute_trending_score(post)
    db.commit()

    data = serialize_post(post, db)
    await manager.broadcast_new_post(data)
    return data


@router.post("/{post_id}/like", response_model=schemas.ReactionOut)
async def like_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_user)
):
    post = db.query(models.Post).filter(models.Post.id == post_id, models.Post.is_removed == False).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = db.query(models.Reaction).filter(
        models.Reaction.user_id == current_user.id,
        models.Reaction.post_id == post_id
    ).first()

    if existing:
        if existing.reaction_type == "like":
            db.delete(existing)
            post.likes = max(0, post.likes - 1)
            msg = "Like removed"
        else:
            existing.reaction_type = "like"
            post.dislikes = max(0, post.dislikes - 1)
            post.likes += 1
            msg = "Changed to like"
    else:
        db.add(models.Reaction(user_id=current_user.id, post_id=post_id, reaction_type="like"))
        post.likes += 1
        msg = "Liked"

    post.trending_score = compute_trending_score(post)
    db.commit()
    await manager.broadcast_reaction(post_id, post.likes, post.dislikes)
    return schemas.ReactionOut(message=msg, likes=post.likes, dislikes=post.dislikes)


@router.post("/{post_id}/dislike", response_model=schemas.ReactionOut)
async def dislike_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_user)
):
    post = db.query(models.Post).filter(models.Post.id == post_id, models.Post.is_removed == False).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = db.query(models.Reaction).filter(
        models.Reaction.user_id == current_user.id,
        models.Reaction.post_id == post_id
    ).first()

    if existing:
        if existing.reaction_type == "dislike":
            db.delete(existing)
            post.dislikes = max(0, post.dislikes - 1)
            msg = "Dislike removed"
        else:
            existing.reaction_type = "dislike"
            post.likes = max(0, post.likes - 1)
            post.dislikes += 1
            msg = "Changed to dislike"
    else:
        db.add(models.Reaction(user_id=current_user.id, post_id=post_id, reaction_type="dislike"))
        post.dislikes += 1
        msg = "Disliked"

    post.trending_score = compute_trending_score(post)
    db.commit()
    await manager.broadcast_reaction(post_id, post.likes, post.dislikes)
    return schemas.ReactionOut(message=msg, likes=post.likes, dislikes=post.dislikes)


@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_user)
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    post.is_removed = True
    db.commit()
    return {"message": "Post removed"}
