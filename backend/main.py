from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend import backend_router

app = FastAPI(
    title="EAGL API",
    description="Poverty Relief and Livestock Delivery Management System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(backend_router)
