"""Modulo per il parsing, la pulizia e il caricamento dei dati bancari."""

import pandas as pd
import re
import shutil
from pathlib import Path
from typing import Optional, Tuple
import config

class DataParser:
    """Gestisce il caricamento, la pulizia e il salvataggio dei file bancari."""

    def __init__(self) -> None:
        """Inizializza il parser compilando le espressioni regolari per le performance."""
        self.column_map: dict[str, str] = config.COLUMN_MAP
        self.inverse_column_map: dict[str, str] = {v: k for k, v in self.column_map.items()}
        
        self.GOLDEN_RULES: dict[str, str] = {
            "EBAY": "EXTRA", "AFFITTO": "CASA", 
            "TIM": "ABBONAMENTI", "DISNEY": "ABBONAMENTI",
            "AMAZON": "SHOPPING", "LIDL": "ALIMENTARI", "CONAD": "ALIMENTARI",
            "TIGRE": "ALIMENTARI", "EMOLUMENTI": "STIPENDIO",
            "FARMACIA": "SALUTE"
        }

        self._regex_payment = re.compile(r'PAGAMENTO (POS|ON LINE)')
        self._regex_transfer = re.compile(r'BONIFICO SEPA (ISTANTANEO|SEE|TRN)')
        self._regex_trn = re.compile(r'TRN [A-Z0-9]+')
        self._regex_bank_codes = re.compile(r'(BACRIT|BPPIIT)[A-Z0-9]+')
        self._regex_locations = re.compile(r'HOOFDDORP|NLD|USA|GBR|ITA|TOUKYOTO')
        self._regex_dates = re.compile(r'\d{2}/\d{2}/\d{2,4}')
        self._regex_decimals = re.compile(r'\d{2}\.\d{2}')
        self._regex_numbers = re.compile(r' N\. \d+')
        
        self.ignore_words: set[str] = {
            "DA", "APP", "POSTEPAY", "ESE", "ESERCENTE", "ADDEBITO", 
            "ACCREDITO", "COMMISSIONE", "PER", "A", "MESE", "DI"
        }

    def extract_merchant(self, description: str) -> str:
        """Estrae un nome pulito rimuovendo rumore bancario (TRN, codici, ecc.).

        Args:
            description (str): La descrizione grezza della banca.

        Returns:
            str: Il nome dell'esercente pulito (max 2 parole).
        """
        if pd.isna(description): 
            return "Sconosciuto"
        
        desc = str(description).upper()
        desc = self._regex_payment.sub('', desc)
        desc = self._regex_transfer.sub('', desc)
        desc = self._regex_trn.sub('', desc)
        desc = self._regex_bank_codes.sub('', desc)
        desc = self._regex_locations.sub('', desc)
        desc = self._regex_dates.sub('', desc)
        desc = self._regex_decimals.sub('', desc)
        desc = self._regex_numbers.sub('', desc)
        
        words = desc.strip().split()
        if words:
            filtered = [w for w in words if w not in self.ignore_words and len(w) > 2]
            return " ".join(filtered[:2]) if filtered else "Altro"
        return "Altro"

    def clean_dataframe(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """Pulisce il DataFrame formattando date e convertendo le stringhe in numeri.

        Args:
            df_raw (pd.DataFrame): DataFrame grezzo caricato dal file utente.

        Returns:
            pd.DataFrame: DataFrame pulito pronto per l'analisi.
        """
        df = df_raw.copy()
        df.columns = [str(c).strip() for c in df.columns]
        df = df.rename(columns=self.column_map)
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce', format='mixed')
        
        if df['amount'].dtype == object:
            df['amount'] = df['amount'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
        else:
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            
        df = df.dropna(subset=['date', 'amount'])
        df['month_year'] = df['date'].dt.to_period('M')
        df['type'] = df['amount'].apply(lambda x: 'Entrata' if x > 0 else 'Uscita')
        df['merchant'] = df['description'].apply(self.extract_merchant)
        return df

    def categorize_new_data(self, existing_data: pd.DataFrame, new_data: pd.DataFrame) -> pd.DataFrame:
        """Assegna automaticamente una categoria ai nuovi movimenti basandosi sullo storico.

        Args:
            existing_data (pd.DataFrame): Il database storico esistente.
            new_data (pd.DataFrame): Le nuove righe caricate.

        Returns:
            pd.DataFrame: Il nuovo DataFrame con le categorie assegnate.
        """
        merchant_to_cat = existing_data.groupby('merchant')['category'].agg(lambda x: x.value_counts().index[0]).to_dict() if not existing_data.empty else {}
        for idx, row in new_data.iterrows():
            desc = str(row['description']).upper()
            assigned_cat = next((cat for kw, cat in self.GOLDEN_RULES.items() if kw in desc), None)
            if assigned_cat: 
                new_data.at[idx, 'category'] = assigned_cat
            else:
                suggested = merchant_to_cat.get(row['merchant'], 'Altro')
                new_data.at[idx, 'category'] = 'Altro' if row['amount'] < 0 and suggested == 'STIPENDIO' else suggested
        return new_data

    def merge_and_deduplicate(self, existing_data: pd.DataFrame, new_data: pd.DataFrame) -> pd.DataFrame:
        """Unisce dati storici e nuovi, rimuovendo le operazioni duplicate.

        Args:
            existing_data (pd.DataFrame): Storico base.
            new_data (pd.DataFrame): Nuovi caricamenti.

        Returns:
            pd.DataFrame: DataFrame fuso e de-duplicato.
        """
        combined = pd.concat([existing_data, new_data], ignore_index=True)
        combined['date_norm'] = pd.to_datetime(combined['date']).dt.normalize()
        combined = combined.drop_duplicates(subset=['date_norm', 'amount', 'description'], keep='first')
        return combined.drop(columns=['date_norm']).sort_values(by='date', ascending=False)

    def load_data(self, file_path: Path | str) -> Optional[pd.DataFrame]:
        """Carica i dati dal file Excel o CSV di configurazione.

        Args:
            file_path (Path | str): Percorso assoluto del file.

        Returns:
            Optional[pd.DataFrame]: Il DataFrame caricato, oppure None se fallisce.
        """
        path_str = str(file_path)
        try:
            df = pd.read_excel(path_str) if path_str.lower().endswith(('.xlsx', '.xls')) else pd.read_csv(path_str, sep=None, engine='python', encoding='latin1')
            return self.clean_dataframe(df).sort_values(by='date', ascending=False)
        except Exception: 
            return None

    def save_to_excel(self, df: pd.DataFrame, file_path: Path | str) -> Tuple[bool, int]:
        """Salva il DataFrame su file, creando prima un backup per prevenire corruzione.

        Args:
            df (pd.DataFrame): Il DataFrame da salvare.
            file_path (Path | str): Il percorso di destinazione.

        Returns:
            Tuple[bool, int]: Esito dell'operazione e numero di righe salvate.
        """
        try:
            path_obj = Path(file_path)
            
            # 1. Creazione file di backup
            if path_obj.exists():
                backup_path = path_obj.with_name(f"{path_obj.stem}_backup{path_obj.suffix}")
                shutil.copy(path_obj, backup_path)

            # 2. Processo di salvataggio
            df_to_save = df.copy()
            df_to_save['date_str'] = df_to_save['date'].dt.strftime('%d/%m/%Y')
            df_to_save = df_to_save.rename(columns={
                'date_str': self.inverse_column_map['date'], 
                'amount': self.inverse_column_map['amount'], 
                'description': self.inverse_column_map['description'], 
                'category': self.inverse_column_map['category']
            })
            export_columns = [self.inverse_column_map[k] for k in ['date', 'amount', 'description', 'category']]
            df_to_save[export_columns].to_excel(str(path_obj), index=False)
            
            return True, len(df)
        except Exception: 
            return False, 0