from typing import List, Optional
from sqlalchemy.orm import Session
from . import models

# --- Course CRUD ---

def get_courses(db: Session) -> List[models.ORMCourse]:
    return list(db.query(models.ORMCourse).all())

def create_course(db: Session, course: models.CourseCreate) -> models.ORMCourse:
    db_course = models.ORMCourse(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

def update_course(db: Session, course_id: int, course: models.CourseCreate) -> Optional[models.ORMCourse]:
    db_course = db.query(models.ORMCourse).filter(models.ORMCourse.id == course_id).first()
    if not db_course:
        return None
    
    for key, value in course.model_dump().items():
        setattr(db_course, key, value)
    
    db.commit()
    db.refresh(db_course)
    return db_course

def delete_course(db: Session, course_id: int) -> bool:
    db_course = db.query(models.ORMCourse).filter(models.ORMCourse.id == course_id).first()
    if not db_course:
        return False
    db.delete(db_course)
    db.commit()
    return True

