from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from twi.db.base import Base


class Subreddit(Base):
    __tablename__ = "subreddits"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    posts: Mapped[list["Post"]] = relationship(back_populates="subreddit")


class Topic(Base):
    __tablename__ = "topics"
    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(200), default="")
    keywords: Mapped[str] = mapped_column(String(500), default="")


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (UniqueConstraint("reddit_id", name="uq_posts_reddit_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    reddit_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    subreddit_id: Mapped[int] = mapped_column(ForeignKey("subreddits.id"))
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(String, default="")
    author: Mapped[str | None] = mapped_column(String(64), nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    num_comments: Mapped[int] = mapped_column(Integer, default=0)
    created_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    subreddit: Mapped["Subreddit"] = relationship(back_populates="posts")


class PipelineState(Base):
    __tablename__ = "pipeline_state"
    subreddit_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    last_fetched_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SentimentScore(Base):
    __tablename__ = "sentiment_scores"
    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), unique=True)
    vader_score: Mapped[float] = mapped_column(default=0.0)
    transformer_score: Mapped[float] = mapped_column(default=0.0)