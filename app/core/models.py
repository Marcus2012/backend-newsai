"""
SQLAlchemy ORM Models
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum


Base = declarative_base()


def generate_uuid():
    """Generate UUID string for MySQL compatibility"""
    return str(uuid.uuid4())


class StatusEnum(str, enum.Enum):
    """Article status enumeration"""
    pending_review = "pending_review"
    draft = "draft"
    published = "published"


class RawArticle(Base):
    """Model for raw scraped articles"""
    __tablename__ = "raw_articles"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    source = Column(String(255), nullable=False, index=True)
    source_url = Column(Text, nullable=False)
    scraped_title = Column(Text, nullable=True)
    scraped_body = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    context = Column(Text, nullable=True)
    raw_json = Column(JSON, nullable=True)
    scraper_template = Column(String(255), nullable=True)
    scraper_version = Column(String(50), nullable=True)
    scraped_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    generated_articles = relationship("GeneratedArticle", back_populates="raw_article")
    
    def __repr__(self):
        return f"<RawArticle(id={self.id}, source={self.source})>"


class GeneratedArticle(Base):
    """Model for AI-generated articles"""
    __tablename__ = "generated_articles"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    raw_article_id = Column(String(36), ForeignKey("raw_articles.id"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    seo_meta = Column(JSON, nullable=True)
    image_url = Column(Text, nullable=True)
    status = Column(Enum(StatusEnum), default=StatusEnum.draft, index=True)
    wp_post_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    raw_article = relationship("RawArticle", back_populates="generated_articles")
    
    def __repr__(self):
        return f"<GeneratedArticle(id={self.id}, title={self.title[:30]}...)>"


class ScraperTemplate(Base):
    """Model for scraper templates per domain"""
    __tablename__ = "scraper_templates"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    selectors = Column(JSON, nullable=False)
    rules = Column(JSON, nullable=True)
    version = Column(String(50), default="1.0")
    active = Column(String(5), default="true")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f"<ScraperTemplate(id={self.id}, domain={self.domain})>"
