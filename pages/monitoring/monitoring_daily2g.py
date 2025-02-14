import dash
from dash import html, Input, Output
from dash.dependencies import State
import dash_bootstrap_components as dbc
import requests

dash.register_page(__name__)

layout = html.Div([
    html.H1('Ini page Monitoring Daily 2G'),
    html.Div('This is our page Monitoring Daily 2G'),
    html.Br(),
    dbc.Button("Export to PDF", id="export-pdf-btn", color="primary"),
])