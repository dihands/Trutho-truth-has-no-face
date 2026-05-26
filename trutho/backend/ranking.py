from datetime import datetime
from sqlalchemy.orm import Session
import models


def compute_trending_score(post: models.Post) -> float:
    """
    Trutho trending score formula:
    score = (likes * 3) + (comments * 4) + (views * 0.1) - age_decay
    age_decay = hours_old * 0.5
    """
    now = datetime.utcnow()
    hours_old = max(0, (now - post.created_at).total_seconds() / 3600)
    comment_count = len(post.comments) if post.comments else 0

    score = (
        (post.likes * 3)
        + (comment_count * 4)
        + (post.views * 0.1)
        - (hours_old * 0.5)
    )
    return round(score, 4)


def update_all_scores(db: Session):
    posts = db.query(models.Post).filter(models.Post.is_removed == False).all()
    for post in posts:
        post.trending_score = compute_trending_score(post)
        # Auto community-verify posts with high engagement
        if post.likes >= 50 and post.verification_status == "unverified":
            post.verification_status = "community_verified"
            post.verification_score = min(1.0, post.likes / 100)
    db.commit()


def get_trending_posts(db: Session, limit: int = 20):
    update_all_scores(db)
    return (
        db.query(models.Post)
        .filter(models.Post.is_removed == False)
        .order_by(models.Post.trending_score.desc())
        .limit(limit)
        .all()
    )
