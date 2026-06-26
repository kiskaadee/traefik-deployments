import os
import psutil
import docker
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from . import models

# Initialize Docker client
try:
    docker_client = docker.from_env()
except Exception:
    docker_client = None

def get_system_stats() -> Dict[str, Any]:
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    disk_path = '/home' if os.path.exists('/home') else '/'
    disk = psutil.disk_usage(disk_path)
    return {
        "cpu": cpu,
        "ram_total": round(ram.total / (1024**3), 2),
        "ram_used": round(ram.used / (1024**3), 2),
        "ram_percent": ram.percent,
        "disk_total": round(disk.total / (1024**3), 2),
        "disk_used": round(disk.used / (1024**3), 2),
        "disk_percent": disk.percent
    }

def get_docker_services() -> Dict[str, List[Dict[str, Any]]]:
    services_config = {
        "infrastructure": [
            {"name": "Traefik", "container": "traefik", "href": "https://traefik.arch-services.mywire.org"},
            {"name": "Authelia", "container": "authelia", "href": "https://auth.arch-services.mywire.org"},
            {"name": "Portainer", "container": "portainer", "href": "https://portainer.arch-services.mywire.org"},
            {"name": "Dozzle", "container": "dozzle", "href": "https://logs.arch-services.mywire.org"},
        ],
        "applications": [
            {"name": "Gitea", "container": "gitea", "href": "https://gitea.arch-services.mywire.org"},
            {"name": "Ollama", "container": "ollama-ollama-1", "href": "https://ollama.arch-services.mywire.org"},
            {"name": "Excalidraw", "container": "excalidraw-excalidraw-1", "href": "https://excalidraw.arch-services.mywire.org"},
            {"name": "Mermaid", "container": "mermaid-live-editor", "href": "https://mermaid.arch-services.mywire.org"},
            {"name": "Jellyfin", "container": "jellyfin", "href": "https://jellyfin.arch-services.mywire.org"},
        ]
    }
    
    results: Dict[str, List[Dict[str, Any]]] = {"infrastructure": [], "applications": []}
    
    if not docker_client:
        for category, services in services_config.items():
            for s in services:
                results[category].append({**s, "status": "unknown"})
        return results

    for category, services in services_config.items():
        for s in services:
            try:
                container = docker_client.containers.get(s["container"])
                status = str(container.status)
            except Exception:
                status = "unknown"
            results[category].append({**s, "status": status})
            
    return results

def get_bookmarks() -> Dict[str, List[Dict[str, str]]]:
    return {
        "Developer": [{"name": "Github", "href": "https://github.com/"}],
        "Social": [{"name": "Reddit", "href": "https://reddit.com/"}],
        "Entertainment": [{"name": "YouTube", "href": "https://youtube.com/"}]
    }

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
