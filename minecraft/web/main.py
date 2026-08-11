import os
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import database
from routers import auth, users, admin

app = FastAPI(title="Minecraft Identity Manager API")

# Include Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)

# Readiness middleware to block API requests until database is ready
@app.middleware("http")
async def db_readiness_middleware(request: Request, call_next):
    # Only intercept /api/ requests
    if request.url.path.startswith("/api/") and not database.DB_READY:
        return JSONResponse(
            status_code=503,
            content={"detail": "Authentication system is initializing, please try again shortly."}
        )
    return await call_next(request)

# Asynchronous background loop to poll database readiness
async def database_polling_loop():
    while not database.check_db_ready():
        await asyncio.sleep(2)

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(database_polling_loop())

@app.get("/", response_class=HTMLResponse)
def index():
    templates_dir = "/app/templates"
    with open(os.path.join(templates_dir, "index.html"), "r") as f:
        return f.read()
