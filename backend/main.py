from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as audit_router

app = FastAPI(
    title="Financial AI Auditor API",
    description="API para auditoría multimodal y validación contable de documentos financieros",
    version="1.0.0"
)

origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audit_router, prefix="/api/v1", tags=["Auditoría"])
