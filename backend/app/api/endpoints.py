from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.services.audit_service import FinancialAuditorService
from app.schemas.schemas import AuditResult

MAXIMO_10_MB = 10 * 1024 * 1024

router = APIRouter()
auditor = FinancialAuditorService()

@router.post("/audit", response_model=AuditResult)
async def audit_document_endpoint(file: UploadFile =  File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail=f"Formato '{file.content_type}' no soportado. Usa JPEG, PNG o WebP."
    )

    image_bytes = await file.read()

    if len(image_bytes) > MAXIMO_10_MB:
        raise HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail="El archivo supera el límite de 10 MB."
    )
    
    resultado = auditor.audit_document(image_bytes)

    return resultado