"""Modulo di configurazione globale per la Finance Dashboard AI Pro."""

from pathlib import Path

# --- PERCORSI FILE ---
BASE_DIR: Path = Path(__file__).parent.resolve()
DATA_DIR: Path = BASE_DIR / "data"
DATA_FILE: Path = DATA_DIR / "dati_finanziari.xlsx"

# --- MAPPATURA COLONNE ---
COLUMN_MAP: dict[str, str] = {
    "Data Contabile": "date",
    "Importo (euro)": "amount",
    "Descrizione operazioni": "description",
    "Categoria": "category"
}

# --- STILI E COLORI UI ---
COLORS: dict[str, str] = {
    "background": "#f4f7f6",
    "primary": "#007BFF",
    "income": "#28a745",
    "expense": "#dc3545",
}
CHART_THEME: str = "plotly_white"

# --- CONFIGURAZIONE STIPENDIO E RICORRENZE ---
EXPECTED_SALARY: float = 1716.0    
SALARY_DAY: int = 21               
SALARY_KEYWORDS: list[str] = ["STIPENDIO", "MANES"]