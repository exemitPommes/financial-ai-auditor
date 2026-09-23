from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Literal

class BoundingBox(BaseModel):
    xmin: int = Field(ge= 0, le=1000, description="Coordinada normalizada eje abscisas izquierda (0-1000)")
    ymin: int = Field(ge= 0, le=1000, description="Coordinada normalizada eje ordenadas superior (0-1000)")
    xmax: int = Field(ge= 0, le=1000, description="Coordinada normalizada eje abscisas derecha (0-1000)")
    ymax: int = Field(ge= 0, le=1000, description="Coordinada normalizada eje ordenadas inferior (0-1000)")

    @model_validator(mode="after")
    def diagonal_validator(self) -> "BoundingBox":
        if self.xmin >= self.xmax:
            raise ValueError(f"La coordinada xmin {self.xmin} debe ser menor que xmax {self.xmax}")
        if self.ymin >= self.ymax:
            raise ValueError(f"La coordinada ymin {self.ymin} debe ser menor que ymax {self.ymax}")
        return self

class DocumentItem(BaseModel):
    description: str
    cantidad: Optional[float] = 1.0
    precio_unitario: Optional[float] = None
    importe_total: float
    bounded_box: Optional[BoundingBox] = Field(None, description="Coordenadas de los puntos que conforman la diagonal del rectangulo que envuelve el item")

class FinancialExtraction(BaseModel):
    tipo_documento: str = Field(description="Factura, Recibo, Ticket, Albarán, etc.")
    empresa_emisora: str
    identificador_fiscal: Optional[str] = Field(None, description="CIF, NIF o Tax ID del emisor")
    fecha_emision: Optional[str] = None
    importe_subtotal: Optional[float] = None
    importe_impuestos: Optional[float] = None
    importe_total: float
    importe_total_bounded_box: Optional[BoundingBox] = Field(None, description="Coordenadas visuales de la caja pertinentes al importe total")
    items: List[DocumentItem] = Field(default_factory=list)

class AuditResult(BaseModel):
    datos: FinancialExtraction
    estado: Literal['AUTO_APPROVED','FLAGGED_FOR_REVIEW'] = Field(description="'AUTO_APPROVED' o 'FLAGGED_FOR_REVIEW'")
    alertas: List[str] = Field(default_factory=list, description="Descadres o irregularidades detectadas")
    tiempo_procesamiento_ms: float