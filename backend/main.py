import os
from pathlib import Path
from app.services.audit_service import FinancialAuditorService
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

"""
def main():
    auditor = FinancialAuditorService()
    
    document_name = "test_w_cif_img.png"
    BASE_DIR = Path(__file__).resolve().parent
    document_test = BASE_DIR / "tests" / "fixtures" / document_name
    print(f"Ruta absoluta calculada: {document_test}")

    if not os.path.exists(document_test):
        print(f"⚠️ Por favor, coloca un documento de prueba con nombre {document_name}")
    else:
        print(f"📄 Procesando '{document_name}' con Vertex AI ({auditor.model_name})...")
        resultado = auditor.audit_document(document_test)

        print("\n" + "="*50)
        print(f"ESTADO DE AUDITORÍA: {resultado.estado}")
        print(f"TIEMPO DE PROCESAMIENTO: {resultado.tiempo_procesamiento_ms} ms")
        print("="*50)

        if resultado.alertas:
            print("\n🚨 ALERTAS DETECTADAS:")
            for alerta in resultado.alertas:
                print(f" - {alerta}")
        else:
            print("\n✅ Documento cuadrado a la perfección. Sin anomalías.")

        print("\n--- JSON ESTRUCTURADO DEVUELTO ---")
        print(resultado.datos.model_dump_json(indent=2))

if __name__ == "__main__":
    main()
"""