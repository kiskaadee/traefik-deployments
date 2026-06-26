import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from . import models, database, routes

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Create tables
    models.Base.metadata.create_all(bind=database.engine)
    
    # Seed initial data if empty
    db = database.SessionLocal()
    try:
        if db.query(models.ORMCourse).count() == 0:
            initial_courses = [
                models.ORMCourse(
                    title="Desarrollo Backend con Python",
                    description="Platzi Learning Path",
                    main_link="https://platzi.com/mis-rutas/16609931/",
                    status="WIP"
                ),
                models.ORMCourse(
                    title="Amazon Junior Software Developer",
                    description="Coursera Professional Certificate",
                    main_link="https://www.coursera.org/professional-certificates/amazon-junior-software-developer",
                    status="WIP"
                ),
                models.ORMCourse(
                    title="Software Design and Architecture",
                    description="Coursera Specialization",
                    main_link="https://www.coursera.org/specializations/software-design-architecture",
                    status="WIP"
                )
            ]
            db.add_all(initial_courses)
            db.commit()
    finally:
        db.close()
    
    yield

app = FastAPI(title="Learning Hub API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)

@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Learning Hub API is running. Use the main dashboard to access the Kanban board."}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
