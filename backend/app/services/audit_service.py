import os
import io
import time
from dotenv import load_dotenv
from PIL import Image
from google import genai
from google.genai import types
from app.schemas.schemas import FinancialExtraction, AuditResult

load_dotenv(override=True)

class FinancialAuditorService:
    def __init__(self):
        self.client = genai.Client(
            vertexai=True,
            project=os.getenv("GCP_PROJECT_ID"),
            location=os.getenv("GCP_LOCATION", "europe-west1")
        )
        self.model_name = os.getenv("MODEL_NAME", "gemini-3.5-flash")

    def _audit_business_rules(self, datos: FinancialExtraction) -> tuple[str, list[str]]:
        alertas = []
        tolerancia = 0.02

        if datos.importe_subtotal is not None and datos.importe_impuestos is not None:
            suma_importes = datos.importe_subtotal + datos.importe_impuestos
            if abs(suma_importes - datos.importe_total) > tolerancia:
                alertas.append(
                    f"Descuadre fiscal: Subtotal ( {datos.importe_subtotal:.2f}€) + "
                    f"Impuestos ( {datos.importe_impuestos:.2f}€) = {suma_importes:.2f}€, "
                    f"pero el Importe total declarado es {datos.importe_total:.2f}€."
                )

        if datos.items:
            suma_items = sum(item.importe_total for item in datos.items)
            suma_comparacion_documento = datos.importe_subtotal if datos.importe_subtotal is not None else datos.importe_total
            if abs(suma_items - suma_comparacion_documento) > tolerancia:
                alertas.append(
                    f"Descuadre de conceptos: La suma de las líneas individuales ({suma_items:.2f}€) "
                    f"no coincide con los detalles del documento ({suma_comparacion_documento:.2f}€)."
                )

        if not datos.identificador_fiscal or len(datos.identificador_fiscal.strip()) < 5:
            alertas.append("Alerta de cumplimiento: No se ha detectado un CIF/NIF válido del emisor.")

        estado = "AUTO_APPROVED" if len(alertas) == 0 else "FLAGGED_FOR_REVIEW"
        return estado, alertas

    def audit_document(self, image_route: str) -> AuditResult:
        inicio = time.time()
        image = Image.open(image_route)

        systemPrompt = """
        Eres un auditor contable y fiscal experto. Analiza minuciosamente la imagen de este documento financiero. Para ello sigue los pasos:
        1 .- Extrae todos los campos requeridos con máxima fidelidad numérica.
        2 .- Para cada línea/concepto y para el importe total, estima sus coordenadas normalizadas visuales (bounding boxes normalizadas del 0 al 1000).
        """

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[image, systemPrompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FinancialExtraction,
                temperature=0.2
            ),
        )

        datos_extraidos: FinancialExtraction = response.parsed

        estado, alertas = self._audit_business_rules(datos_extraidos)
        tiempo_total_ms = (time.time() - inicio) * 1000

        return AuditResult(
            datos = datos_extraidos,
            estado = estado,
            alertas = alertas,
            tiempo_procesamiento_ms = round(tiempo_total_ms, 2)
        )

    @staticmethod
    def process_bytes_to_image(image_bytes: bytes) -> Image.Image:
        image_stream = io.BytesIO(image_bytes)
        processed_image = Image.open(image_stream)
        processed_image.load()
        return processed_image

    def audit_document(self, image_bytes_api: bytes) -> AuditResult:
        inicio = time.time()
        image = self.process_bytes_to_image(image_bytes_api)
        

        systemPrompt = """
        Eres un auditor contable y fiscal experto. Analiza minuciosamente la imagen de este documento financiero. Para ello sigue los pasos:
        1 .- Extrae todos los campos requeridos con máxima fidelidad numérica.
        2 .- Para cada línea/concepto y para el importe total, estima sus coordenadas normalizadas visuales (bounding boxes normalizadas del 0 al 1000).
        """

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[image, systemPrompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FinancialExtraction,
                temperature=0.2
            ),
        )

        datos_extraidos: FinancialExtraction = response.parsed

        estado, alertas = self._audit_business_rules(datos_extraidos)
        tiempo_total_ms = (time.time() - inicio) * 1000

        return AuditResult(
            datos = datos_extraidos,
            estado = estado,
            alertas = alertas,
            tiempo_procesamiento_ms = round(tiempo_total_ms, 2)
        )