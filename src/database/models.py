from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    domain = Column(String, default="general")
    row_count = Column(Integer)
    column_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to features
    features = relationship("FeatureSuggestion", back_populates="dataset")


class FeatureSuggestion(Base):
    __tablename__ = "feature_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    column_name = Column(String, index=True)
    idea = Column(String)
    reason = Column(Text)
    code_snippet = Column(Text)
    improvement_score = Column(Float, nullable=True)  # E.g., validation metric bump
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to dataset
    dataset = relationship("Dataset", back_populates="features")
