import os
from app.services.audit_service import FinancialAuditorService

def main():
    auditor = FinancialAuditorService()
    
    document_name = "old_ticket_test.png"
    document_test = "./backend/app/tests/{document_name}"

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