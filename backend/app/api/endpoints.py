from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.core.database import init_db, registrar_decision
from app.schemas.schemas import AuditResult, AuditorDecisionRequest, AuditorDecisionResponse
from app.services.audit_service import FinancialAuditorService
from app.services.compliance_service import ComplianceService

ALLOWED_MIMES = ["image/jpeg", "image/png", "image/webp", "application/pdf"]
MAXIMO_10_MB = 10 * 1024 * 1024

init_db()
router = APIRouter()
auditor = FinancialAuditorService()
cumplimiento_normativo = ComplianceService()

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

    alertas_cumplimiento_normativo = cumplimiento_normativo.check_compliance(items=resultado.datos.items)
    resultado.alertas.extend(alertas_cumplimiento_normativo)

    if alertas_cumplimiento_normativo:
        resultado.estado = "FLAGGED_FOR_REVIEW"

    return resultado

@router.post("/decision", response_model=AuditorDecisionResponse)
async def registrar_decision_auditor(payload: AuditorDecisionRequest):
    datos = payload.auditoria.datos
    
    nuevo_id = registrar_decision(
        dictamen_ia=payload.auditoria.estado,
        decision_humana=payload.decision,
        comentario=payload.comentario,
        datos_completos_json=payload.auditoria.model_dump_json(),
        empresa=datos.empresa_emisora,
        cif=datos.identificador_fiscal,
        total=datos.importe_total
    )

    return AuditorDecisionResponse(
        id_registro=nuevo_id,
        mensaje=f"Decisión '{payload.decision}' registrada con éxito en el libro contable.",
        fecha_registro=datetime.now().isoformat()
    )
