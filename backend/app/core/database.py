import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent.parent / "auditorias.db"

def init_db():
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auditorias_registro (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_registro TEXT NOT NULL,
                empresa_emisora TEXT,
                cif_nif TEXT,
                importe_total REAL,
                dictamen_ia TEXT NOT NULL,
                decision_humana TEXT NOT NULL,
                comentario_humano TEXT,
                json_completo TEXT NOT NULL
            );
        """)
        connection.commit()

def registrar_decision(
    dictamen_ia: str,
    decision_humana: str,
    comentario: str | None,
    datos_completos_json: str,
    empresa: str | None,
    cif: str | None,
    total: float
) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO auditorias_registro (
                fecha_registro,
                empresa_emisora,
                cif_nif,
                importe_total,
                dictamen_ia,
                decision_humana,
                comentario_humano,
                json_completo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            datetime.now().isoformat(),
            empresa,
            cif,
            total,
            dictamen_ia,
            decision_humana,
            comentario,
            datos_completos_json
        ))
        conn.commit()
        return cursor.lastrowid