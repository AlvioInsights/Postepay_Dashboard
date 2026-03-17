"""Modulo per la generazione dei grafici Plotly."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import config

def create_monthly_bar(trend_data: pd.DataFrame) -> go.Figure:
    """Crea un grafico a barre raggruppate per l'andamento mensile di entrate e uscite.

    Args:
        trend_data (pd.DataFrame): DataFrame contenente le colonne 'month_year_str', 
                                   'Entrata', 'Uscita' e 'Saldo'.

    Returns:
        go.Figure: Grafico Plotly generato.
    """
    fig = go.Figure()
    fig.add_trace(go.Bar(x=trend_data['month_year_str'], y=trend_data['Entrata'], name='Entrate', marker_color=config.COLORS['income']))
    fig.add_trace(go.Bar(x=trend_data['month_year_str'], y=trend_data['Uscita'], name='Uscite', marker_color=config.COLORS['expense']))
    fig.add_trace(go.Scatter(x=trend_data['month_year_str'], y=trend_data['Saldo'], name='Saldo', line=dict(color='black', width=2)))
    fig.update_layout(template=config.CHART_THEME, height=300, barmode='group', margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig

def create_pie_chart(category_data: pd.DataFrame, title: str, color_scale: str = 'Reds') -> go.Figure:
    """Crea un grafico a torta per la distribuzione delle spese o entrate.

    Args:
        category_data (pd.DataFrame): DataFrame con colonne 'amount' e 'category'.
        title (str): Titolo del grafico.
        color_scale (str, optional): Scala di colori ('Reds' o 'Greens'). Defaults to 'Reds'.

    Returns:
        go.Figure: Grafico Plotly generato.
    """
    palette = px.colors.sequential.Reds if color_scale == 'Reds' else px.colors.sequential.Greens
    fig = px.pie(category_data, values='amount', names='category', hole=0.4, color_discrete_sequence=palette)
    fig.update_layout(title=title, template=config.CHART_THEME, height=300, margin=dict(l=10, r=10, t=40, b=10))
    return fig

def create_forecast_chart(forecast_data: pd.DataFrame) -> go.Figure:
    """Crea un grafico lineare per la proiezione del saldo.

    Args:
        forecast_data (pd.DataFrame): DataFrame con colonne 'type', 'date', 'balance'.

    Returns:
        go.Figure: Grafico Plotly con dati reali storici e linea tratteggiata per la previsione.
    """
    fig = go.Figure()
    real_data = forecast_data[forecast_data['type'] == 'Reale']
    fig.add_trace(go.Scatter(x=real_data['date'], y=real_data['balance'], name='Saldo Reale', line=dict(color=config.COLORS['primary'], width=3)))
    predicted_data = forecast_data[forecast_data['type'] == 'Previsione']
    fig.add_trace(go.Scatter(x=predicted_data['date'], y=predicted_data['balance'], name='Simulazione', line=dict(color='gray', width=2, dash='dash', shape='hv')))
    fig.update_layout(template=config.CHART_THEME, height=300, margin=dict(l=10, r=10, t=30, b=10), hovermode='x unified')
    return fig

def create_merchant_bar(merchant_data: pd.DataFrame, category_name: str = "Tutte") -> go.Figure:
    """Crea un grafico a barre orizzontali per i top esercenti.

    Args:
        merchant_data (pd.DataFrame): DataFrame con colonne 'amount' e 'merchant'.
        category_name (str, optional): Nome della categoria per il titolo. Defaults to "Tutte".

    Returns:
        go.Figure: Grafico Plotly generato.
    """
    fig = px.bar(merchant_data, x='amount', y='merchant', orientation='h', color='amount', color_continuous_scale='Reds')
    fig.update_layout(title=f"Top Esercenti: {category_name}", template=config.CHART_THEME, height=300, margin=dict(l=10, r=10, t=40, b=10), coloraxis_showscale=False)
    return fig