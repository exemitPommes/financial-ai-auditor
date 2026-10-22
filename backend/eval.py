import json
import time
from pathlib import Path
from app.services.audit_service import FinancialAuditorService
from app.services.compliance_service import ComplianceService

BASE_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = BASE_DIR / "tests" / "fixtures"
GROUND_TRUTH_PATH = BASE_DIR / "tests" / "ground_truth.json"

def run_benchmark():
    if not GROUND_TRUTH_PATH.exists():
        print(f"❌ No se encontró: {GROUND_TRUTH_PATH}")
        return

    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    auditor = FinancialAuditorService()
    compliance = ComplianceService()

    total_cases = len(ground_truth)
    correct_status = 0
    correct_rag_evals = 0
    total_rag_expected = 0
    false_positives = 0
    latencies = []

    print("\n" + "=" * 95)
    print(f"{'ID':<6} | {'ARCHIVO':<32} | {'ESPERADO':<12} | {'OBTENIDO':<12} | {'RAG OK?':<8} | {'ESTADO':<5} | {'LATENCIA':<8}")
    print("=" * 95)

    for item in ground_truth:
        case_id = item["case_id"]
        base_name = Path(item["file_name"]).stem
        
        file_path = FIXTURES_DIR / f"{base_name}.png"
        if not file_path.exists():
            file_path = FIXTURES_DIR / f"{base_name}.pdf"

        if not file_path.exists():
            print(f"{case_id:<6} | {item['file_name']:<32} | NO ENCONTRADO EN tests/fixtures/")
            continue

        mime_type = "application/pdf" if file_path.suffix == ".pdf" else "image/png"
        
        with open(file_path, "rb") as f:
            doc_bytes = f.read()

        t0 = time.time()
        
        # 1. Pipeline de extracción y reglas
        resultado = auditor.audit_document(doc_bytes, mime_type)
        
        # 2. Pipeline de RAG
        alertas_rag = compliance.check_compliance(resultado.datos.items)
        resultado.alertas.extend(alertas_rag)
        if alertas_rag:
            resultado.estado = "FLAGGED_FOR_REVIEW"

        elapsed = (time.time() - t0) * 1000
        latencies.append(elapsed)

        status_ok = resultado.estado == item["expected_status"]
        if status_ok:
            correct_status += 1

        if item["expected_status"] == "AUTO_APPROVED" and resultado.estado != "AUTO_APPROVED":
            false_positives += 1

        expected_rag = item["expected_rag_rules"]
        rag_ok = True
        if expected_rag:
            total_rag_expected += len(expected_rag)
            for rule in expected_rag:
                found = any(rule in alerta for alerta in resultado.alertas)
                if found:
                    correct_rag_evals += 1
                else:
                    rag_ok = False
        else:
            if any("[CUMPLIMIENTO NORMATIV]" in alerta for alerta in resultado.alertas):
                rag_ok = False

        status_icon = "☑" if status_ok else "✖︎"
        rag_icon = "☑" if rag_ok else "✖︎"

        print(f"{case_id:<6} | {file_path.name[:30]:<32} | {item['expected_status'][:10]:<12} | {resultado.estado[:10]:<12} | {rag_icon:<8} | {status_icon:<5} | {elapsed:.0f} ms")

    # Métricas consolidadas
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    accuracy = (correct_status / total_cases) * 100 if total_cases else 0
    rag_recall = (correct_rag_evals / total_rag_expected) * 100 if total_rag_expected else 100.0

    print("\n" + "=" * 95)
    print("BENCHMARK Y EVALUACIÓN EXPERIMENTAL DE LA PILA DE TESTS")
    print("=" * 95)
    print(f"Total Casos Evaluados:                 {total_cases}")
    print(f"Exactitud de Decisión (Accuracy):      {accuracy:.1f}% ({correct_status}/{total_cases})")
    print(f"Falsos Positivos (FPR):                {false_positives} caso(s)")
    print(f"Sensibilidad RAG (Policy Recall):      {rag_recall:.1f}% ({correct_rag_evals}/{total_rag_expected})")
    print(f"Latencia Media End-to-End:             {avg_latency:.0f} ms")
    print("=" * 95)

if __name__ == "__main__":
    run_benchmark()