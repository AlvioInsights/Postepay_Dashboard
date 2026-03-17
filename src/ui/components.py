"""Componenti UI riutilizzabili per la dashboard."""

from dash import html
import dash_bootstrap_components as dbc

def create_metric_card(title: str, value: float, color: str, icon: str) -> dbc.Card:
    """Crea una card KPI stilizzata per visualizzare metriche finanziarie.

    Args:
        title (str): Il titolo della metrica (es. "Entrate Periodo").
        value (float): Il valore numerico da visualizzare.
        color (str): Il colore esadecimale o la classe colore Bootstrap.
        icon (str): Il nome dell'icona Bootstrap (es. "arrow-up-circle").

    Returns:
        dbc.Card: Il componente Dash Bootstrap Card pronto per il layout.
    """
    formatted_value: str = f"€ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"bi bi-{icon} me-2"),
                html.Span(title, className="text-muted small uppercase font-weight-bold")
            ], className="d-flex align-items-center mb-2"),
            html.H2(formatted_value, style={"color": color, "fontWeight": "bold"})
        ])
    ], className="metric-card mb-4")