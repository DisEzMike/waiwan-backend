from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import os

from .database.db import db

from .routes import auth_router, user_router, search_router, job_router, chat_router, file_router

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

@app.get("/chat-test", response_class=HTMLResponse)
async def chat_test():
    """Serve the WebSocket chat test page"""
    html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "websocket_test.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Test page not found</h1>", status_code=404)

@app.get("/file-test", response_class=HTMLResponse)
async def file_test():
    """Serve the file upload test page"""
    html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "file_upload_test.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>File upload test page not found</h1>", status_code=404)


app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(search_router.router)
app.include_router(job_router.router)
app.include_router(chat_router.router)
app.include_router(file_router.router)