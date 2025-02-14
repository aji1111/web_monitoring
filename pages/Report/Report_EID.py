import dash
from dash import html

dash.register_page(__name__)

layout = html.Div([
    html.H1('Ini page Report to EID'),
    html.Div('This is our page Report to EID'),
])