import os
import re
import chromadb
from pathlib import Path
from google import genai
from google.genai import types
from typing import TypedDict, List
from dotenv import load_dotenv
from app.schemas.schemas import DocumentItem, ComplianceReport

load_dotenv(override=True)

class ListaCumplimientoNormativo(TypedDict):
    conceptos_facturas: str
    normas_internas: List[str]

class ComplianceService:
    def __init__(self):
        self.ai_client = genai.Client(
            vertexai=True,
            project=os.getenv("GCP_PROJECT_ID"),
            location=os.getenv("GCP_LOCATION", "europe-west1")
        )
        self.embedding_model = "text-embedding-004"
        self.model_name = os.getenv("MODEL_NAME", "gemini-3.5-flash")

        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.get_or_create_collection(name='expense_policies')

        policies = []
        ids = []
        output_dir = Path(__file__).parent.parent / "knowledge"
        file_path = output_dir / "politica_gastos.md"

        with open(file_path, 'r', encoding='UTF-8') as base_knowledge:
            raw_chunks = re.split(r"(?=### \[POL-)", base_knowledge.read())
        for chunk in raw_chunks:
            if not chunk.strip().startswith("### [POL-"):
                continue
            clean_text = chunk.split("---")[0].strip()
            match = re.search(r"POL-\d+\.\d+", clean_text)
            if match:
                ids.append(match.group(0))
                policies.append(clean_text)

        print("Vectorizando normas con Vertex AI (text-embedding-004)...")
        policy_vectors = self._embed_texts(policies)
        self.collection.add(
            ids=ids,
            documents=policies,
            embeddings=policy_vectors
            #metadatas=[{'seccion': 'Dietas y Manutención'}, {'seccion': 'Dietas y Manutención'}, {'seccion': 'Gastos No Reembolsables y Uso Personal'}, {'seccion': 'Gastos No Reembolsables y Uso Personal'}, {'seccion': 'Suministros de Oficina y Servicios Operativos'}, {'seccion': 'Suministros de Oficina y Servicios Operativos'}]
        )

    def check_compliance(self, items: list[DocumentItem]) -> list[str]:
        alertas_politica = []
        descripcion_items: str = ", ".join(item.description for item in items)
        
        posibles_infracciones = self.search_applicable_policies(descripcion_items, n_results=2)
        numero_coincidencias = len(posibles_infracciones['ids'])
        if numero_coincidencias == 0:
            return []
        else:
            """ lista_cumplimiento_normativo: ListaCumplimientoNormativo = {
                'conceptos_facturas': descripcion_items,
                'normas_internas': []
            } """
            normas_encontradas = []
            for norma_id, texto_norma in zip(posibles_infracciones['ids'][0], posibles_infracciones['documents'][0]):
                normas_encontradas.append(f"{norma_id}: {texto_norma}")
            """ for indice in range(numero_coincidencias):
                norma_id = posibles_infracciones['ids'][0][indice]
                texto_norma = posibles_infracciones['documents'][0][indice]
                lista_cumplimiento_normativo['normas_internas'].append(norma_id + ' ' + texto_norma) """

            system_prompt = """
            Actúa como un auditor de cumplimiento normativo. A continuación tienes una lista de conceptos facturados y las normas internas de la empresa. 
            Determina si algún concepto infringe alguna norma. Si hay infracción, responde con un JSON indicando la norma infringida y el motivo. 
            Si todo cumple, devuelve una lista vacía.
            """

            prompt_usuario = f"""
            CONCEPTOS FACTURADOS EN EL DOCUMENTO:
            {descripcion_items}
            
            NORMAS INTERNAS APLICABLES:
            {chr(10).join(normas_encontradas)}
            """

            response = self.ai_client.models.generate_content(
                model=self.model_name,
                contents=[system_prompt, prompt_usuario],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ComplianceReport,
                    temperature=0.1
                ),
            )
            print("\nRespuesta Gemini:")
            print(f"{response}")

            reporte: ComplianceReport = response.parsed;

            if len(reporte.infracciones) == 0:
                return []
            else:
                for infraccion in reporte.infracciones:
                    alertas_politica.append(f"[COMPLIANCE] Infracción de {infraccion.norma_id}: {infraccion.motivo}")
    
        #elif numero_coincidencias == 1:
            #alertas_politica.append(
                #f"[COMPLIANCE] Violación de la norma {infracciones['documents'][0]}"
            #)
        #else:
            #for indice in numero_coincidencias:
                #norma_id = resultado['ids'][0][indice]
                #texto_norma = resultado['documents'][0][indice]
                #alertas_politica.append(
                    #f"[COMPLIANCE] Violación de la norma {norma_id}: {texto_norma}"
                #)
        return alertas_politica

    def search_applicable_policies(self, query_text: str, n_results: int = 1):
        query_vector = self._embed_texts([query_text])[0]

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=n_results
        )
        return results

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = self.ai_client.models.embed_content(
            model=self.embedding_model,
            contents=texts,
        )
        return [embeddings.values for embeddings in response.embeddings]


if __name__ == "__main__":
    print("Iniciando prueba de la clase...")
    servicio = ComplianceService()

    items_tramposos = [
        DocumentItem(
            description="Liquid foundation",
            cantidad=50,
            precio_unitario=2.75,
            importe_total=137.5,
        ),
        DocumentItem(
            description="Lipstick",
            cantidad=100,
            precio_unitario=0.75,
            importe_total=74.75,
        ),
    ]

    print("\n🚨 Probando con factura de Cosmética (Shadow Beauty)...")
    resultado = servicio.check_compliance(items=items_tramposos)