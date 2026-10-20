import os
import io
import time
import re
import base64
import pypdfium2 as pdfium
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image
from google import genai
from google.genai import types
from app.schemas.schemas import FinancialExtraction, AuditResult

load_dotenv(override=True)

CIF_ES_REGEX = r"^[ABCDEFGHJKLMNPQRSUVW][0-9]{7}[0-9A-J]$"
MARGEN_MAXIMO_DIAS = 180
TIPOS_IVA_VALIDOS = {
    21.0: "General (21%)",
    10.0: "Reducido (10%)",
    4.0:  "Superreducido (4%)",
    0.0:  "Exento (0%)"
}
TIPOS_DOCUMENTO_SIMPLIFICADO = {'Ticket', 'Recibo'}

class FinancialAuditorService:
    def __init__(self):
        self.client = genai.Client(
            vertexai=True,
            project=os.getenv("GCP_PROJECT_ID"),
            location=os.getenv("GCP_LOCATION", "europe-west1")
        )
        self.model_name = os.getenv("MODEL_NAME", "gemini-3.5-flash")

    @staticmethod
    def _pdf_to_base64_image(pdf_bytes: bytes) -> str:
        pdf = pdfium.PdfDocument(pdf_bytes)
        page = pdf[0]
        pil_image = page.render(scale=2).to_pil()
        
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=85)
        encoded_bytes = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        return f"data:image/jpeg;base64,{encoded_bytes}"

    @staticmethod
    def _general_rules(datos: FinancialExtraction, tolerancia: float) -> list[str]:
        alertas_general = []
        if datos.importe_subtotal is not None and datos.importe_impuestos is not None:
            suma_importes = datos.importe_subtotal + datos.importe_impuestos
            if round(abs(suma_importes - datos.importe_total), 2) > tolerancia:
                    alertas_general.append(
                        f"[ARITMÉTICA] Descuadre en totales: Subtotal ( {datos.importe_subtotal:.2f}€) + "
                        f"Impuestos ( {datos.importe_impuestos:.2f}€) = {suma_importes:.2f}€, "
                        f"pero el Importe total declarado es {datos.importe_total:.2f}€."
                    )
        
        if datos.items and datos.importe_total is not None:
            suma_items = sum(item.importe_total for item in datos.items)
                    
            cuadra_con_subtotal = (
                datos.importe_subtotal is not None
                and round(abs(suma_items - datos.importe_subtotal), 2) <= tolerancia
                )
            cuadra_con_total = round(abs(suma_items - datos.importe_total), 2) <= tolerancia
        
            if not (cuadra_con_subtotal or cuadra_con_total):
                base_esperada = datos.importe_subtotal if datos.importe_subtotal is not None else datos.importe_total
                alertas_general.append(
                    f"[ARITMÉTICA] Descuadre de conceptos: La suma de las líneas individuales ({suma_items:.2f}€) "
                    f"no coincide con los detalles del documento ({base_esperada:.2f}€)."
                )
        
        if not datos.identificador_fiscal:
            alertas_general.append("[FISCAL] Ausencia de CIF/NIF del emisor en el documento.")
        else:
            id_fiscal = re.sub(r"[\s-]", "", datos.identificador_fiscal.upper())
            if not re.match(CIF_ES_REGEX, id_fiscal):
                alertas_general.append(f"[FISCAL] Formato de CIF/NIF no conforme a la normativa española: '{datos.identificador_fiscal}'.")
        return alertas_general

    @staticmethod
    def _time_constriction_rules(datos: FinancialExtraction) -> list[str]:
        alertas_fechas = []
        if not datos.fecha_emision:
            return alertas_fechas
        
        fecha_emision = None
        for formato_fecha in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                fecha_emision = datetime.strptime(datos.fecha_emision.strip(), formato_fecha).date()
                break
            except ValueError:
                continue

        if not fecha_emision:
            alertas_fechas.append(f"[TEMPORAL] Formato de fecha no reconocible: '{datos.fecha_emision}'.")
            return alertas_fechas
        
        fecha_actual = datetime.now().date()
        dias_transcurridos = (fecha_actual - fecha_emision).days

        if dias_transcurridos < 0:
            alertas_fechas.append(
                f"[TEMPORAL] Fecha anómala en el futuro: {datos.fecha_emision} (posterior a {fecha_actual.strftime('%d/%m/%Y')})."
            )
        elif dias_transcurridos > MARGEN_MAXIMO_DIAS:
            alertas_fechas.append(
                f"[TEMPORAL] Documento fuera de plazo: emitido hace {dias_transcurridos} días (límite: {MARGEN_MAXIMO_DIAS} días)."
            )
            
        return alertas_fechas

    @staticmethod
    def _item_value_rules(datos: FinancialExtraction, tolerancia: float) -> list[str]:
        alertas_item = []
        for item in datos.items:
            if item.cantidad is not None and item.precio_unitario is not None:
                importe_item_total = item.cantidad * item.precio_unitario
                if round(abs(importe_item_total - item.importe_total), 2) > tolerancia:
                    alertas_item.append(
                        f"[ARITMÉTICA] Error de cálculo en  '{ item.description }': "
                        f"{ item.cantidad } x {item.precio_unitario:.2f}€ = {importe_item_total:.2f}€, "
                        f"pero figura {item.importe_total:.2f}€."
                    )

                if importe_item_total < 0:
                    alertas_item.append(
                        f"[ARITMÉTICA] Concepto con importe negativo no justificado: '{item.description}' ({item.importe_total:.2f}€)."
                    )
        return alertas_item

    @staticmethod
    def _taxes_rules(datos: FinancialExtraction) -> list[str]:
        alertas_iva = []
        if datos.importe_impuestos is not None and datos.importe_subtotal is not None and datos.importe_subtotal > 0:
            tasa_calculada = ( datos.importe_impuestos / datos.importe_subtotal ) * 100
            es_iva_legal = any(abs(tasa_calculada - tipo) <= 0.5 for tipo in TIPOS_IVA_VALIDOS)
            if not es_iva_legal:
                alertas_iva.append(
                    f"[FISCAL] Tasa impositiva calculada anómala ({tasa_calculada:.1f}%). "
                    f"No corresponde a tipos de IVA vigentes (21%, 10%, 4%, 0%)."
                )
        return alertas_iva

    @staticmethod
    def _acceptance_threshold_rules(datos: FinancialExtraction) -> list[str]:
        alertas_acceptance = []
        documento_valido = datos.tipo_documento in TIPOS_DOCUMENTO_SIMPLIFICADO or datos.tipo_documento is None
        if documento_valido and datos.importe_total > 400.0:
            alertas_acceptance.append(
                f"[REGULATORIO] Factura simplificada excede el límite legal de 400.00€ "
                f"(Total: {datos.importe_total:.2f}€). Requiere factura ordinaria con datos del receptor."
            )
        return alertas_acceptance


    def _audit_business_rules(self, datos: FinancialExtraction) -> tuple[str, list[str]]:
        alertas = []
        tolerancia = 0.02

        alertas.extend(self._general_rules(datos, tolerancia))
        alertas.extend(self._time_constriction_rules(datos))
        alertas.extend(self._item_value_rules(datos, tolerancia))
        alertas.extend(self._taxes_rules(datos))
        alertas.extend(self._acceptance_threshold_rules(datos))

        estado = "AUTO_APPROVED" if len(alertas) == 0 else "FLAGGED_FOR_REVIEW"
        return estado, alertas

    def audit_document(self, document_bytes: bytes, mime_type: str) -> AuditResult:
        inicio = time.time()
        preview_image = None
        es_multipage = False

        if mime_type == "application/pdf":
            preview_image = self._pdf_to_base64_image(document_bytes)
            pdf = pdfium.PdfDocument(document_bytes)
            if len(pdf) > 1:
                es_multipage = True
        
        document_part = types.Part.from_bytes(
            data = document_bytes, 
            mime_type = mime_type
        )

        systemPrompt = """
        Eres un auditor contable y fiscal experto. Analiza minuciosamente la imagen de este documento financiero. Para ello sigue los pasos:
        1 .- Extrae todos los campos requeridos con máxima fidelidad numérica.
        2 .- Para cada línea/concepto y para el importe total, estima sus coordenadas normalizadas visuales (bounding boxes normalizadas del 0 al 1000).
        """

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[document_part, systemPrompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FinancialExtraction,
                temperature=0.2
            ),
        )

        datos_extraidos: FinancialExtraction = response.parsed
        if es_multipage:
            alertas.append("[SISTEMA] Documento multipágina: la inspección visual se limita a la primera página.")

        estado, alertas = self._audit_business_rules(datos_extraidos)
        tiempo_total_ms = (time.time() - inicio) * 1000

        return AuditResult(
            datos = datos_extraidos,
            estado = estado,
            alertas = alertas,
            tiempo_procesamiento_ms = round(tiempo_total_ms, 2),
            preview_image_base64=preview_image
        )
    
    """ local testing """
    def audit_document_local(self, image_route: str) -> AuditResult:
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