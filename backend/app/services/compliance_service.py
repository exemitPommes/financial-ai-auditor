import os
import re
import chromadb
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv
from app.schemas.schemas import DocumentItem, ComplianceReport

load_dotenv(override=True)

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

        policy_vectors = self._embed_texts(policies)
        self.collection.add(
            ids=ids,
            documents=policies,
            embeddings=policy_vectors
        )

    def check_compliance(self, items: list[DocumentItem]) -> list[str]:
        alertas_politica = []
        descripcion_items: str = ", ".join(item.description for item in items)
        
        posibles_infracciones = self.search_applicable_policies(descripcion_items, n_results=2)
        numero_coincidencias = len(posibles_infracciones['ids'])
        if numero_coincidencias == 0:
            return []
        else:
            normas_encontradas = []
            for norma_id, texto_norma in zip(posibles_infracciones['ids'][0], posibles_infracciones['documents'][0]):
                normas_encontradas.append(f"{norma_id}: {texto_norma}")

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

            reporte: ComplianceReport = response.parsed;

            if len(reporte.infracciones) == 0:
                return []
            else:
                for infraccion in reporte.infracciones:
                    alertas_politica.append(f"[CUMPLIMIENTO NORMATIVO] Infracción de {infraccion.norma_id}: {infraccion.motivo}")

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
