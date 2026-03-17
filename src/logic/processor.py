"""Modulo contenente le funzioni pure per l'elaborazione dei dati e il calcolo dei KPI."""

import pandas as pd
from typing import Any, Tuple, Optional
import config

def filter_data(df: pd.DataFrame, start_date: Optional[str] = None, end_date: Optional[str] = None, categories: Optional[list[str]] = None) -> pd.DataFrame:
    """Filtra il DataFrame in base a data e categorie selezionate.

    Args:
        df (pd.DataFrame): Il DataFrame originale.
        start_date (Optional[str], optional): Data inizio in formato stringa. Defaults to None.
        end_date (Optional[str], optional): Data fine in formato stringa. Defaults to None.
        categories (Optional[list[str]], optional): Lista di categorie ammesse. Defaults to None.

    Returns:
        pd.DataFrame: Il DataFrame filtrato.
    """
    filtered_df = df.copy()
    if start_date: 
        filtered_df = filtered_df[filtered_df['date'] >= pd.to_datetime(start_date)]
    if end_date: 
        filtered_df = filtered_df[filtered_df['date'] <= pd.to_datetime(end_date)]
    if categories: 
        filtered_df = filtered_df[filtered_df['category'].isin(categories)]
    return filtered_df

def get_kpis(filtered_df: pd.DataFrame, full_df: pd.DataFrame) -> dict[str, Any]:
    """Calcola i Key Performance Indicators (Entrate, Uscite, Saldo, Forecast).

    Args:
        filtered_df (pd.DataFrame): Il DataFrame filtrato (per entrate/uscite del periodo).
        full_df (pd.DataFrame): Il DataFrame completo (per calcolo saldo totale e burn rate).

    Returns:
        dict[str, Any]: Dizionario contenente tutti i KPI calcolati.
    """
    if full_df.empty: 
        return {"income": 0.0, "expense": 0.0, "balance": 0.0, "savings_rate": 0.0, "forecast": 0.0, "burn_rate": 0.0, "salary_added": False}
    
    ref_date = full_df['date'].max()
    current_balance = full_df['amount'].sum()
    
    mask_90 = (full_df['date'] > (ref_date - pd.Timedelta(days=90))) & (full_df['type'] == 'Uscita')
    daily_burn = abs(full_df[mask_90]['amount'].sum() / 90)
    
    days_left = ((ref_date + pd.offsets.MonthEnd(0)) - ref_date).days
    if days_left <= 0: days_left = 30
    projected_bal = current_balance - (daily_burn * days_left)
    
    curr_month = full_df[full_df['month_year'] == ref_date.to_period('M')]
    salary_received = curr_month[(curr_month['amount'] >= config.EXPECTED_SALARY * 0.8) | (curr_month['description'].str.upper().apply(lambda x: any(kw in x for kw in config.SALARY_KEYWORDS)))]
    
    salary_added = False
    if ref_date.day < config.SALARY_DAY and salary_received.empty:
        projected_bal += config.EXPECTED_SALARY
        salary_added = True

    return {
        "income": round(filtered_df[filtered_df['amount'] > 0]['amount'].sum(), 2),
        "expense": round(abs(filtered_df[filtered_df['amount'] < 0]['amount'].sum()), 2),
        "balance": round(current_balance, 2), "savings_rate": 0.0,
        "forecast": round(projected_bal, 2), "burn_rate": round(daily_burn, 2),
        "salary_added": salary_added
    }

def get_daily_balance_with_forecast(full_df: pd.DataFrame) -> pd.DataFrame:
    """Genera i dati storici e futuri per il grafico del saldo previsionale.

    Args:
        full_df (pd.DataFrame): Il DataFrame completo dei movimenti.

    Returns:
        pd.DataFrame: DataFrame contenente 'date', 'balance' e 'type' (Reale o Previsione).
    """
    if full_df.empty: return pd.DataFrame()
    history = full_df.groupby('date')['amount'].sum().sort_index().cumsum().reset_index()
    history.columns = ['date', 'balance']; history['type'] = 'Reale'
    
    ref_date = full_df['date'].max()
    curr_bal = history['balance'].iloc[-1]
    
    mask_90 = (full_df['date'] > (ref_date - pd.Timedelta(days=90))) & (full_df['type'] == 'Uscita')
    daily_burn = abs(full_df[mask_90]['amount'].sum() / 90)
    
    end_f = (ref_date + pd.offsets.MonthEnd(0))
    if ref_date == end_f: end_f = (ref_date + pd.Timedelta(days=30))
    future_days = pd.date_range(start=ref_date, end=end_f)
    
    curr_month = full_df[full_df['month_year'] == ref_date.to_period('M')]
    salary_rec = curr_month[(curr_month['amount'] >= config.EXPECTED_SALARY * 0.8) | (curr_month['description'].str.upper().apply(lambda x: any(kw in x for kw in config.SALARY_KEYWORDS)))]
    
    future_points = []
    temp_bal = curr_bal
    salary_applied = not salary_rec.empty

    for d in future_days:
        if d == ref_date: continue
        temp_bal -= daily_burn
        if d.day == config.SALARY_DAY and not salary_applied:
            temp_bal += config.EXPECTED_SALARY
            salary_applied = True
        future_points.append({'date': d, 'balance': temp_bal, 'type': 'Previsione'})
        
    future_df = pd.DataFrame(future_points)
    last_real = history.tail(1).copy(); last_real['type'] = 'Previsione'
    return pd.concat([history, last_real, future_df], ignore_index=True)

def search_merchant_stats(df: pd.DataFrame, query: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Tuple[Optional[dict], Optional[pd.DataFrame]]:
    """Esegue una ricerca testuale sugli esercenti e restituisce statistiche.

    Args:
        df (pd.DataFrame): DataFrame dei dati.
        query (str): Stringa di ricerca.
        start_date (Optional[str], optional): Filtro data inizio. Defaults to None.
        end_date (Optional[str], optional): Filtro data fine. Defaults to None.

    Returns:
        Tuple[Optional[dict], Optional[pd.DataFrame]]: Un dizionario con i totali e un DataFrame coi dettagli.
    """
    if not query or len(query) < 3: return None, None
    # Sicurezza: regex=False previene vulnerabilità ReDoS su input utente malevolo
    mask = df['description'].str.contains(query, case=False, na=False, regex=False)
    result_df = df[mask].copy()
    if start_date: result_df = result_df[result_df['date'] >= pd.to_datetime(start_date)]
    if end_date: result_df = result_df[result_df['date'] <= pd.to_datetime(end_date)]
    if result_df.empty: return None, None
    
    stats = {"total": abs(result_df[result_df['amount'] < 0]['amount'].sum()), "freq": len(result_df), "name": query.upper()}
    table_data = result_df.sort_values('date', ascending=False).head(10).copy()
    table_data['Data'] = table_data['date'].dt.strftime('%d/%m/%y')
    return stats, table_data[['Data', 'amount', 'description']]

def get_top_merchants(df: pd.DataFrame, category: Optional[str] = None) -> pd.DataFrame:
    """Restituisce i primi 10 esercenti per volume di spesa."""
    dff = df[df['type'] == 'Uscita'].copy()
    if category: dff = dff[dff['category'] == category]
    if dff.empty: return pd.DataFrame(columns=['merchant', 'amount'])
    return dff.groupby('merchant')['amount'].sum().abs().reset_index().sort_values('amount', ascending=False).head(10)

def get_transaction_list(df: pd.DataFrame) -> pd.DataFrame:
    """Formatta il DataFrame per l'esportazione e la tabella UI."""
    if df.empty: return pd.DataFrame(columns=['Data', 'Esercente', 'Categoria', 'Importo', 'Descrizione'])
    dff = df.copy().sort_values('date', ascending=False)
    dff['Data'] = dff['date'].dt.strftime('%d/%m/%Y')
    return dff[['Data', 'merchant', 'category', 'amount', 'description']].rename(columns={'merchant':'Esercente','category':'Categoria','amount':'Importo','description':'Descrizione'})

def get_monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Aggrega i dati per creare il trend mensile storico."""
    monthly = df.copy(); monthly['month_year_str'] = monthly['date'].dt.strftime('%Y-%m')
    trend = monthly.groupby(['month_year_str', 'type'])['amount'].sum().unstack(fill_value=0).reset_index()
    if 'Entrata' not in trend.columns: trend['Entrata'] = 0.0
    if 'Uscita' not in trend.columns: trend['Uscita'] = 0.0
    trend['Uscita'] = trend['Uscita'].abs(); trend['Saldo'] = trend['Entrata'] - trend['Uscita']
    return trend.sort_values('month_year_str')

def get_category_distribution(df: pd.DataFrame, trans_type: str = 'Uscita') -> pd.DataFrame:
    """Restituisce la distribuzione delle categorie per entrate o uscite."""
    return df[df['type'] == trans_type].groupby('category')['amount'].sum().abs().reset_index().sort_values('amount', ascending=False)

def get_month_comparison(full_df: pd.DataFrame, filtered_df: pd.DataFrame) -> Tuple[pd.DataFrame, str, str]:
    """Confronta il mese corrente con quello precedente."""
    if filtered_df.empty: return pd.DataFrame(), "", ""
    curr_m = filtered_df['month_year'].max(); prev_m = curr_m - 1
    curr_n, prev_n = curr_m.strftime('%b %y'), prev_m.strftime('%b %y')
    expenses = full_df[full_df['type'] == 'Uscita']
    comp = pd.DataFrame({'Corrente': expenses[expenses['month_year'] == curr_m].groupby('category')['amount'].sum().abs(), 'Precedente': expenses[expenses['month_year'] == prev_m].groupby('category')['amount'].sum().abs()}).fillna(0)
    comp['Variazione %'] = 0.0; mask = comp['Precedente'] != 0
    comp.loc[mask, 'Variazione %'] = ((comp['Corrente'] - comp['Precedente']) / comp['Precedente'] * 100).round(1)
    return comp.reset_index().rename(columns={'index': 'category'}).sort_values('Corrente', ascending=False), curr_n, prev_n