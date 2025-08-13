from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector

# Database URL
import os
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/eda_photos")
print(f"Using DATABASE_URL: {DATABASE_URL}")

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for declarative class definitions
Base = declarative_base()

# Table for storing image embeddings
class ImageEmbedding(Base):
    __tablename__ = "image_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    image_name = Column(String, unique=True, index=True)
    embedding = Column(Vector(768))  # ViT-L/14 has 768-dim embeddings

# Table for storing face embeddings
class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    image_name = Column(String, index=True)
    face_index = Column(Integer)  # index of face within image
    box = Column(JSON)  # {top, right, bottom, left}
    embedding = Column(Vector(128))

# Cache for face group clusters stored as JSON
class FaceGroupsCache(Base):
    __tablename__ = "face_groups_cache"

    id = Column(Integer, primary_key=True)
    data = Column(JSON)  # {"clusters": {"<label>": ["<filename>", ...]}, "total_clusters": <int>}

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 