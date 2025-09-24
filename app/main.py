from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database.db import db

from .routes import auth_router, user_router, search_router, job_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_extensions()
    db.create_all()
    yield

app = FastAPI(lifespan=lifespan)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(search_router.router)
app.include_router(job_router.router)