from typing import Optional
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

# --- SQLAlchemy ORM Models ---

class ORMCourse(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column()
    description: Mapped[Optional[str]] = mapped_column(nullable=True)
    main_link: Mapped[str] = mapped_column()
    last_link: Mapped[Optional[str]] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(default="Planning")  # WIP, Planning, Archive

# --- Pydantic Validation Models ---

class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    main_link: str
    last_link: Optional[str] = None
    status: str = "Planning"

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
