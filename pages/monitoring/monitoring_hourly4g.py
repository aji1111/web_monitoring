import dash
from dash import html

dash.register_page(__name__)

layout = html.Div([
    html.H1('Ini page Monitoring Hourly 4G'),
    html.Div('This is our page Monitoring Hourly 4G'),
])