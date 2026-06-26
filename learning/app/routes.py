from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from . import models, controllers, database

router = APIRouter(prefix="/api")

@router.get("/system-stats")
def read_system_stats() -> Dict[str, Any]:
    return controllers.get_system_stats()

@router.get("/services")
def read_services() -> Dict[str, Any]:
    return controllers.get_docker_services()

@router.get("/bookmarks")
def read_bookmarks() -> Dict[str, Any]:
    return controllers.get_bookmarks()

@router.get("/courses", response_model=List[models.Course])
def read_courses(db: Session = Depends(database.get_db)) -> List[models.ORMCourse]:
    return controllers.get_courses(db)

@router.post("/courses", response_model=models.Course)
def create_course(course: models.CourseCreate, db: Session = Depends(database.get_db)) -> models.ORMCourse:
    return controllers.create_course(db, course)

@router.put("/courses/{course_id}", response_model=models.Course)
def update_course(course_id: int, course: models.CourseCreate, db: Session = Depends(database.get_db)) -> models.ORMCourse:
    db_course = controllers.update_course(db, course_id, course)
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
    return db_course

@router.delete("/courses/{course_id}")
def delete_course(course_id: int, db: Session = Depends(database.get_db)) -> Dict[str, str]:
    success = controllers.delete_course(db, course_id)
    if not success:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course deleted"}
