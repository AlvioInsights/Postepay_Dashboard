"""Modulo per la definizione della struttura dell'interfaccia utente (UI)."""

from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc

def get_layout(available_categories: list[str]) -> dbc.Container:
    table_columns: list[dict] = [
        {"name": "Data", "id": "Data", "editable": False},
        {"name": "Esercente", "id": "Esercente", "editable": False},
        {"name": "Categoria", "id": "Categoria", "editable": True, "presentation": "dropdown"},
        {"name": "Importo", "id": "Importo", "editable": False},
        {"name": "Descrizione", "id": "Descrizione", "editable": False}
    ]
    dropdown_options = [{'label': c, 'value': c} for c in available_categories]

    return dbc.Container([
        dbc.Row([dbc.Col(html.H1("Finance Dashboard AI Pro", className="text-center my-3 text-primary fw-bold"), width=12)]),
        dbc.Row([dbc.Col(html.Div([dcc.Upload(id='upload-data', children=html.Div(['Trascina file banca qui']), style={'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '2px', 'borderStyle': 'dashed', 'borderRadius': '10px', 'textAlign': 'center', 'backgroundColor': '#f8f9fa'}), html.Div(id='upload-feedback', className="mt-2")], className="p-3 bg-white rounded shadow-sm mb-4"), width=12)]),
        dbc.Row([
            dbc.Col([html.Label("Categorie:", className="fw-bold small"), dcc.Dropdown(id='category-filter', options=dropdown_options, multi=True, className="shadow-sm")], md=6),
            dbc.Col([html.Label("Periodo:", className="fw-bold small"), dcc.DatePickerRange(id='date-filter', display_format='DD/MM/YYYY', className="d-block shadow-sm")], md=6),
        ], className="p-2 bg-white rounded shadow-sm mb-4 mx-0 align-items-center"),
        dbc.Row(id='kpi-row-main', className="mb-2"),
        dbc.Row(id='kpi-row-forecast', className="mb-3", justify="center"),
        dbc.Row([dbc.Col([html.Div([html.H6("ℹ️ Eventi ricorrenti previsti per fine mese:", className="fw-bold text-info mb-2"), html.Div(id="recurring-events-debug", className="small text-muted")], className="p-3 bg-white rounded shadow-sm mb-4 border-start border-info border-4")], width=12)]),
        dbc.Row([dbc.Col(html.Div([html.H6("📊 Confronto Mese Corrente vs Precedente", className="fw-bold mb-2"), html.Div(id="month-comparison-table")], className="p-3 bg-white rounded shadow-sm mb-4"), width=12)]),
        dbc.Row([dbc.Col(html.Div([html.H6("🔮 Proiezione Saldo Fine Mese"), dcc.Graph(id='balance-forecast-chart')], className="p-3 bg-white rounded shadow-sm mb-4"), width=12)]),
        dbc.Row([dbc.Col(html.Div([html.H6("🔍 Ricerca Dettagliata"), dbc.Input(id="search-input", placeholder="Cerca...", type="text", size="sm"), html.Div(id="search-results"), html.Div(id="search-table-container", className="mt-2")], className="p-3 bg-white rounded shadow-sm mb-4"), width=12)]),
        dbc.Row([dbc.Col(html.Div([dcc.Graph(id='merchant-bar-chart')], className="p-2 bg-white rounded shadow-sm mb-4"), width=12)]),
        dbc.Row([dbc.Col(html.Div([html.H6("📈 Trend Mensile Storico"), dcc.Graph(id='monthly-trend-chart')], className="p-2 bg-white rounded shadow-sm mb-4"), width=12)]),
        dbc.Row([
            dbc.Col([html.Div([dcc.Graph(id='category-pie-chart')], className="p-2 bg-white rounded shadow-sm mb-4")], md=6),
            dbc.Col([html.Div([dcc.Graph(id='income-pie-chart')], className="p-2 bg-white rounded shadow-sm mb-4")], md=6),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([html.H6("📜 Registro Dettagliato Movimenti", className="fw-bold d-inline"), dbc.Button("📥 Scarica CSV", id="btn-export", color="success", size="sm", className="float-end ms-2"), dcc.Download(id="download-dataframe-csv")], className="mb-3"),
                    html.Div(id='save-feedback'),
                    dash_table.DataTable(
                        id='main-transaction-table', columns=table_columns, data=[], page_size=15, sort_action="native", filter_action="native", editable=True, 
                        dropdown={'Categoria': {'options': dropdown_options}}, style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}, 
                        style_cell={'textAlign': 'left', 'padding': '8px'}, style_data_conditional=[{'if': {'column_id': 'Importo', 'filter_query': '{Importo} > 0'}, 'color': '#28a745'}, {'if': {'column_id': 'Importo', 'filter_query': '{Importo} < 0'}, 'color': '#dc3545'}]
                    )
                ], className="p-3 bg-white rounded shadow-sm mb-4")
            ], width=12)
        ])
    ], fluid=True, style={"backgroundColor": "#f4f7f6", "padding": "15px"})