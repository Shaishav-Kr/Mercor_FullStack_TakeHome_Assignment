from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./candidates.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, index=True)
    phone = Column(String)
    location = Column(String)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)
    availability = Column(Text)   # JSON str or comma separated
    salary_expectation = Column(Integer)  # numeric USD
    work_experience_raw = Column(Text)   # JSON string
    education_raw = Column(Text)         # JSON string
    skills_raw = Column(Text)            # JSON string
    experience_years = Column(Float, default=0.0)
    score = Column(Float, default=0.0)
    selected = Column(Boolean, default=False)
    reason = Column(Text, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)