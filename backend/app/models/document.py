import datetime
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, synonym
from pgvector.sqlalchemy import Vector
from backend.app.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    document_type = Column(String(50), default="WCR") # WCR, DDR, Mud Report, Geological, Casing, Cementing, Directional Survey
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    page_count = Column(Integer, default=1)
    owner_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    visibility = Column(String(50), default="DEMO", nullable=False) # PRIVATE, ORGANIZATION, SHARED, DEMO
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    upload_date = synonym("created_at")
    is_processed = Column(Boolean, default=True)

    well = relationship("Well", back_populates="documents")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False, index=True)
    extracted_text = Column(Text, nullable=False)
    structured_tables_json = Column(JSON, default=list)
    detected_topics = Column(JSON, default=list)
    metadata_json = Column(JSON, default=dict)

    document = relationship("Document", back_populates="pages")
    chunks = relationship("KnowledgeChunk", back_populates="page", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    page_id = Column(Integer, ForeignKey("document_pages.id"), nullable=True, index=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=True, index=True)
    chunk_index = Column(Integer, default=0)
    chunk_text = Column(Text, nullable=False)
    section_header = Column(String(255), nullable=True)
    depth_reference_m = Column(Float, nullable=True)
    formation_reference = Column(String(100), nullable=True)
    owner_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    visibility = Column(String(50), default="DEMO", nullable=False)
    embedding = Column(Vector(384), nullable=True)

    document = relationship("Document", back_populates="chunks")
    page = relationship("DocumentPage", back_populates="chunks")
