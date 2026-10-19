import { EstadoAuditoria } from './audit.types';

export interface BoundingBox {
    xmin: number;
    ymin: number;
    xmax: number;
    ymax: number;
}

export interface DocumentItem {
    description: string;
    cantidad?: number | null;
    precio_unitario?: number | null;
    importe_total: number;
    bounded_box?: BoundingBox | null;
}

export interface FinancialExtraction {
    tipo_documento: string;
    empresa_emisora: string;
    identificador_fiscal?: string | null;
    fecha_emision?: string | null;
    importe_subtotal?: number | null;
    importe_impuestos?: number | null;
    importe_total: number;
    importe_total_bounded_box?: BoundingBox | null;
    items: DocumentItem[];
}

export interface AuditResult {
    datos: FinancialExtraction;
    estado: EstadoAuditoria;
    alertas: string[];
    tiempo_procedamiento_ms: number;
}

export interface PolicyViolation {
    norma_id: string;
    motivo: string;
}

export interface ComplianceReport {
    infracciones: PolicyViolation[]
}