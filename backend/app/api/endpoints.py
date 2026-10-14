from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.services.audit_service import FinancialAuditorService
from app.schemas.schemas import AuditResult

ALLOWED_MIMES = ["image/jpeg", "image/png", "image/webp", "application/pdf"]
MAXIMO_10_MB = 10 * 1024 * 1024

router = APIRouter()
auditor = FinancialAuditorService()

""" 
Si es PDF nativo o escaneado, se renderiza a imagen página por página (con librerías estándar como pypdf o pdf2image).
Error 400 (Archivo ilegible / corrupto): Error inmediato al frontend: "El archivo no se puede procesar".
"""
@router.post("/audit", response_model=AuditResult)
async def audit_document_endpoint(file: UploadFile =  File(...)):
    if file.content_type not in ALLOWED_MIMES:
        raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail=f"Formato '{file.content_type}' no soportado. Usa PDF, JPEG, PNG o WebP."
    )

    document_bytes = await file.read()

    if len(document_bytes) > MAXIMO_10_MB:
        raise HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail="El archivo supera el límite de 10 MB."
    )
    
    resultado = auditor.audit_document(document_bytes, file.content_type)

    return resultado