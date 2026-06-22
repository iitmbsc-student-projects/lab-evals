"""
Entry point for the Lab Evaluation Application backend.
Initializes FastAPI app, includes API routers, and configures middleware.
"""

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import admin, auth, student, ta, user
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.models.user import User

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure DB and all tables exist
    Base.metadata.create_all(bind=engine)

    # Auto-create admin user on startup
    db = SessionLocal()
    try:
        admin_user = (
            db.query(User).filter_by(email=settings.ADMIN_EMAIL).first()
        )
        if not admin_user:
            admin_user = User(
                name=settings.ADMIN_NAME,
                email=settings.ADMIN_EMAIL,
                is_admin=True,
            )
            db.add(admin_user)
            db.commit()
        else:
            admin_user.is_admin = True
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="Lab Evaluation Application", lifespan=lifespan)

allowed_origins = []

if settings.ENV == "development":
    allowed_origins = ["*"]
else:
    allowed_origins = [settings.FRONTEND_ORIGIN]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    return await call_next(request)


# API Routers
def include_routers(app: FastAPI):
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
    app.include_router(ta.router, prefix="/api/v1/ta", tags=["ta"])
    app.include_router(
        student.router, prefix="/api/v1/student", tags=["student"]
    )
    app.include_router(user.router, prefix="/api/v1/user", tags=["user"])


include_routers(app)


@app.get("/healthz", tags=["health"])
async def health_check():
    return {"status": "ok"}
