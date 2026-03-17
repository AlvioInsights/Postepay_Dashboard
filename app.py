"""
Punto d'ingresso (Entry Point) dell'applicazione Dash.
Gestisce l'inizializzazione del server e tutte le callback interattive.
"""

import dash
from dash import Input, Output, html, dcc, dash_table, State
import dash_bootstrap_components as dbc
import pandas as pd
import base64
import io
from typing import Any

import config
from src.logic.parser import DataParser
import src.logic.processor as processor
from src.ui.layout import get_layout
from src.ui.charts import (
    create_monthly_bar, create_pie_chart, 
    create_forecast_chart, create_merchant_bar
)
from src.ui.components import create_metric_card

# 1. SETUP DELL'APPLICAZIONE
app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP], 
    suppress_callback_exceptions=True,
    title="Finance Dashboard AI Pro"
)

parser = DataParser()

# Caricamento Globale (Adatto solo per uso personale locale su GitHub)
df_raw: pd.DataFrame = parser.load_data(config.DATA_FILE)

if df_raw is None or df_raw.empty:
    df_raw = pd.DataFrame(columns=[
        'date', 'amount', 'description', 'category', 'month_year', 'type', 'merchant'
    ])

available_categories = sorted(df_raw['category'].unique()) if 'category' in df_raw.columns else []
app.layout = get_layout(available_categories)


@app.callback(
    Output('upload-feedback', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def update_database(contents: str, filename: str) -> dash.development.base_component.Component | str:
    """Gestisce l'upload drag-and-drop del file bancario con logica di sicurezza.

    Args:
        contents (str): Stringa Base64 del file caricato.
        filename (str): Nome del file per capirne l'estensione (csv o xlsx).

    Returns:
        Component: Oggetto Alert Bootstrap indicante il successo o l'errore.
    """
    global df_raw
    if contents is None: 
        return ""
        
    # Limite file per prevenire Memory Exhaustion (Sicurezza)
    if len(contents) > 10 * 1024 * 1024:
        return dbc.Alert("Errore: File troppo grande (Max ~7MB reali).", color="danger")

    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        if 'csv' in filename.lower():
            new_df_raw = pd.read_csv(io.StringIO(decoded.decode('latin1', errors='replace')), sep=None, engine='python')
        else:
            new_df_raw = pd.read_excel(io.BytesIO(decoded))
        
        new_df = parser.clean_dataframe(new_df_raw)
        new_df = parser.categorize_new_data(df_raw, new_df)
        
        old_count = len(df_raw)
        df_raw = parser.merge_and_deduplicate(df_raw, new_df)
        parser.save_to_excel(df_raw, config.DATA_FILE)
        
        return dbc.Alert(f"✅ Aggiornato! Aggiunte {len(df_raw) - old_count} operazioni.", color="success", dismissable=True)
    except Exception as e:
        return dbc.Alert(f"Errore caricamento: {str(e)}", color="danger")


@app.callback(
    Output('save-feedback', 'children'),
    Input('main-transaction-table', 'data_timestamp'),
    State('main-transaction-table', 'data'),
    State('main-transaction-table', 'data_previous'),
    prevent_initial_call=True
)
def update_cell(timestamp: int, current_data: list[dict], previous_data: list[dict]) -> dash.development.base_component.Component | str:
    """Modifica e salva le categorie cambiate manualmente nella tabella UI.

    Args:
        timestamp (int): Timestamp evento.
        current_data (list[dict]): Stato attuale della tabella.
        previous_data (list[dict]): Stato precedente della tabella.

    Returns:
        Component: Un Toast di conferma o stringa vuota.
    """
    global df_raw
    if previous_data is None: 
        return ""
    
    for i in range(len(current_data)):
        if current_data[i]['Categoria'] != previous_data[i]['Categoria']:
            row = current_data[i]
            target_mask = (
                (df_raw['date'].dt.strftime('%d/%m/%Y') == row['Data']) & 
                (df_raw['amount'] == row['Importo']) & 
                (df_raw['description'] == row['Descrizione'])
            )
            if target_mask.any():
                df_raw.loc[target_mask, 'category'] = row['Categoria']
                parser.save_to_excel(df_raw, config.DATA_FILE)
                return dbc.Toast("Modifica salvata su file", header="Salvataggio", icon="success", duration=2000, style={"position": "fixed", "top": 66, "right": 10, "width": 350})
    return ""


@app.callback(
    [Output('kpi-row-main', 'children'), Output('kpi-row-forecast', 'children'),
     Output('recurring-events-debug', 'children'), Output('monthly-trend-chart', 'figure'),
     Output('category-pie-chart', 'figure'), Output('income-pie-chart', 'figure'),
     Output('balance-forecast-chart', 'figure'), Output('merchant-bar-chart', 'figure'),
     Output('search-results', 'children'), Output('search-table-container', 'children'),
     Output('month-comparison-table', 'children'), Output('main-transaction-table', 'data')],
    [Input('category-filter', 'value'), Input('date-filter', 'start_date'),
     Input('date-filter', 'end_date'), Input('search-input', 'value'),
     Input('upload-feedback', 'children'), Input('save-feedback', 'children')]
)
def update_dashboard(selected_categories: list[str], start_date: str, end_date: str, search_query: str, up_trig: Any, save_trig: Any) -> tuple:
    """Rigenera tutti i grafici e le tabelle in base ai filtri applicati.

    Args:
        selected_categories (list[str]): Categorie selezionate nel dropdown.
        start_date (str): Data d'inizio filtro.
        end_date (str): Data di fine filtro.
        search_query (str): Testo cercato nella barra di ricerca.
        up_trig (Any): Trigger per refresh post upload.
        save_trig (Any): Trigger per refresh post salvataggio.

    Returns:
        tuple: Multipli output aggiornati per popolare il layout di Dash.
    """
    if df_raw.empty:
        return ([html.Div("Dati non disponibili")] * 2 + [""] + [{}] * 5 + ["", "", {}, []])

    filtered_df = processor.filter_data(df_raw, start_date, end_date, selected_categories)
    kpis = processor.get_kpis(filtered_df, df_raw)
    
    main_kpis = [
        dbc.Col(create_metric_card("Entrate Periodo", kpis['income'], config.COLORS['income'], "arrow-up-circle"), md=4),
        dbc.Col(create_metric_card("Uscite Periodo", kpis['expense'], config.COLORS['expense'], "arrow-down-circle"), md=4),
        dbc.Col(create_metric_card("Saldo Attuale", df_raw['amount'].sum(), config.COLORS['primary'], "wallet2"), md=4)
    ]
    
    forecast_color = config.COLORS['income'] if kpis['forecast'] >= df_raw['amount'].sum() else config.COLORS['expense']
    forecast_kpis = [
        dbc.Col(create_metric_card("Forecast Fine Mese", kpis['forecast'], forecast_color, "crystal-ball"), md=4),
        dbc.Col(create_metric_card("Burn Rate (90gg)", kpis['burn_rate'], "#6c757d", "fire"), md=4)
    ]
    
    debug_msg = html.Span([html.I(className="bi bi-info-circle me-2"), f"Stipendio aggiunto ({config.EXPECTED_SALARY}€)"], className="text-primary fw-bold") if kpis['salary_added'] else html.Span([html.I(className="bi bi-check-circle me-2"), "Stipendio elaborato/Non previsto"], className="text-success")

    fig_trend = create_monthly_bar(processor.get_monthly_trend(filtered_df))
    fig_pie_exp = create_pie_chart(processor.get_category_distribution(filtered_df, 'Uscita'), "Uscite", 'Reds')
    fig_pie_inc = create_pie_chart(processor.get_category_distribution(filtered_df, 'Entrata'), "Entrate", 'Greens')
    fig_forecast = create_forecast_chart(processor.get_daily_balance_with_forecast(df_raw))
    active_cat = selected_categories[0] if selected_categories and len(selected_categories) == 1 else None
    fig_merchants = create_merchant_bar(processor.get_top_merchants(filtered_df, category=active_cat), category_name=active_cat if active_cat else "Tutte")
    
    df_comp, c_name, p_name = processor.get_month_comparison(df_raw, filtered_df)
    comp_layout = html.Div([
        html.P(f"Analisi: {c_name} vs {p_name}", className="text-muted small text-center mb-1"),
        dash_table.DataTable(data=df_comp.to_dict('records'), columns=[{"name": i, "id": i} for i in df_comp.columns], style_table={'height': '200px', 'overflowY': 'auto'}, style_cell={'fontSize': '11px', 'textAlign': 'center'}, style_data_conditional=[{'if': {'column_id': 'Variazione %', 'filter_query': '{Variazione %} > 0'}, 'color': '#dc3545'}, {'if': {'column_id': 'Variazione %', 'filter_query': '{Variazione %} < 0'}, 'color': '#28a745'}])
    ]) if not df_comp.empty else html.P("Seleziona periodo per confronto")

    search_res, search_table = "", ""
    if search_query and len(search_query) >= 3:
        stats, details = processor.search_merchant_stats(df_raw, search_query, start_date, end_date)
        if stats:
            search_res = dbc.Alert(f"Ricerca: {stats['name']} | Spesa Totale: € {stats['total']:,.2f}", color="info", className="py-1 mt-2")
            search_table = dash_table.DataTable(data=details.to_dict('records'), columns=[{"name": i, "id": i} for i in details.columns], page_size=5, style_cell={'fontSize': '10px'})

    table_data = processor.get_transaction_list(filtered_df).to_dict('records')

    return (main_kpis, forecast_kpis, debug_msg, fig_trend, fig_pie_exp, fig_pie_inc, fig_forecast, fig_merchants, search_res, search_table, comp_layout, table_data)


@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-export", "n_clicks"),
    [State('category-filter', 'value'), State('date-filter', 'start_date'), State('date-filter', 'end_date')],
    prevent_initial_call=True
)
def export_data(n_clicks: int, categories: list[str], start_date: str, end_date: str) -> dict:
    """Genera un file CSV dalle transazioni filtrate e lo scarica.

    Args:
        n_clicks (int): Contatore click bottone export.
        categories (list[str]): Categorie filtrate in quel momento.
        start_date (str): Data inizio.
        end_date (str): Data fine.

    Returns:
        dict: Il payload Dash dcc.send_data_frame che innesca il download nel browser.
    """
    export_df = processor.get_transaction_list(processor.filter_data(df_raw, start_date, end_date, categories))
    return dcc.send_data_frame(export_df.to_csv, "bilancio_esportato.csv", index=False)


if __name__ == '__main__':
    print("--- FINANCE DASHBOARD AVVIATA ---")
    app.run(debug=True, port=8050)