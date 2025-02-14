import pyodbc
import pandas as pd
import numpy as np
import sqlalchemy
from sqlalchemy.engine import URL
from dash import Dash, dcc, html, Input, Output, callback, dash_table, no_update, State, callback_context
from dash.dash_table.Format import Format, Scheme, Sign, Symbol
import dash_bootstrap_components as dbc
from collections import OrderedDict
import plotly.express as px
from datetime import date, datetime, timedelta
import dash_ag_grid as dag
pd.options.mode.chained_assignment = None
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import dash
from cachetools import cached
from database import konek_sql_server, dfdail4gnya, uniq_site4g, uniq_sitehourly4g
from fpdf import FPDF
import io
import os, glob
import pdfkit
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer, BaseDocTemplate, Frame, PageTemplate, Paragraph
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet
import time
from plotly.io import write_image
import plotly.io as pio

dash.register_page(__name__, path='/report/report-qc')

# Data SITEID dan DATE_ID
site_ids = uniq_site4g('SITE_ID')
date_ids = uniq_site4g('DATE_ID')

logo_kiri = "/assets/logo_eid.png"
logo_kanan = "/assets/logo_tsel.png"

layout = dbc.Container(
    fluid=True,
    children=[
        # Tabs for navigation
        dbc.Row([
            dbc.Col([
                dcc.Tabs(
                    id="tabs_qc",
                    value='filter_data',
                    children=[
                        dcc.Tab(label='Filter', value='filter_data'),
                        dcc.Tab(label='Acceptance Page', value='acc_page'),
                        dcc.Tab(label='Acceptance Cluster', value='acc_cluster'),
                        dcc.Tab(label='KPI Stat', value='kpi_start'),
                        dcc.Tab(label='KPI Upgrade', value='kpi_upgrade'),
                        dcc.Tab(label='KPI Justification', value='kpi_justif'),
                        dcc.Tab(label='KPI Colo', value='kpi_colo'),
                        dcc.Tab(label='Info TA', value='kpi_ta'),
                        dcc.Tab(label='Chart KPI', value='kpi_chart'),
                        dcc.Tab(label='KPI Cluster', value='kpi_cluster'),
                        dcc.Tab(label='Alarm', value='alarm'),
                        dcc.Tab(label='Config1', value='config1'),
                        dcc.Tab(label='Config2', value='config2'),
                        dcc.Tab(label='Neig1', value='neighbours1'),
                        dcc.Tab(label='Neig2', value='neighbours2'),
                    ]
                ),
            ], width=12),
        ], className="mb-3"),

        # Header with logos
        dbc.Row([
            dbc.Col(html.Img(src=logo_kiri, style={"height": "40px"}), width="auto"),
            dbc.Col(html.Img(src=logo_kanan, style={"height": "40px"}), width="auto"),
        ], justify="between", style={"backgroundColor": "#f8f9fa", "padding": "10px"}),

        # Filter section
        dbc.Row(id="filter-section", children=[
            dbc.Col([
                dcc.Dropdown(
                    options=site_ids,
                    id='filter_Site',
                    multi=True,
                    clearable=True,
                    placeholder="Pilih Site",
                ),
            ], width=12, lg=4),
            dbc.Col([
                dcc.Dropdown(
                    options=['L1800', 'L900', 'L2100', 'L2300'],
                    id='filter_Band',
                    multi=True,
                    clearable=True,
                    placeholder="Pilih Band",
                ),
            ], width=12, lg=4),
            dbc.Col([
                dcc.DatePickerRange(
                    id="date_range",
                    min_date_allowed=min(date_ids),
                    max_date_allowed=max(date_ids),
                    start_date=(max(date_ids) - timedelta(days=30)),
                    end_date=max(date_ids),
                ),
            ], width=12, lg=4),
        ], className="mb-3"),

        # Content section
        dbc.Row([
            dbc.Col(id="tabs_content_qc", width=12),
        ]),

        dcc.Store(id="filter-df-store", data=None),
        dcc.Store(id="filter_Site-dropdown", data=None),
        dcc.Store(id="tabs", data=None)
    ]
)

# Callback to toggle filter section visibility
@callback(
    Output("filter-section", "style"),
    Input("tabs_qc", "value"),
)
def toggle_filter_section(tab):
    if tab != "filter_data":
        return {'display': 'none'}
    return {}

# Callback to render tab content
@callback(
    Output('tabs_content_qc', 'children'),
    [
        Input('tabs_qc', 'value'),
        Input("filter_Site", "value"),
        Input("filter_Band", "value"),
        Input("date_range", "start_date"),
        Input("date_range", "end_date"),
    ],
    prevent_initial_call=True
)
def render_tab_content_qc(tab, select_site, select_band, start_date, end_date):
    ctx = callback_context
    if not ctx.triggered:
        return html.Div("Silahkan klik tab filter dan pilih site, band, dan date untuk menampilkan content.")

    # Default message if no filters are selected
    if not (select_site or select_band):
        return html.Div("Silahkan pilih site, band, dan date untuk menampilkan content.")

    # Render content based on the selected tab
    if tab == "filter_data":
        return html.Div("Silahkan pilih site, band, dan date untuk menampilkan content.")
    
    elif tab == 'acc_page':
        content_acc_page = dbc.Container([
            # Title
            dbc.Row([
                dbc.Col(html.H2("SITE QUALITY ACCEPTANCE CERTIFICATE", style={'textAlign': 'center'}), width=12)
            ], style={'marginBottom': '20px'}),
            
            # Reference No.
            dbc.Row([
                dbc.Col([
                    html.Span("Reference No.:", style={'marginRight': '10px'}),
                    html.Div([
                        html.Div("", style={'display': 'inline-block', 'width': '20px', 'height': '20px', 'border': '1px solid black', 'marginRight': '2px'}) for _ in range(12)
                    ], style={'display': 'inline-block'})
                ], width=12, style={'textAlign': 'left'})
            ], style={'marginBottom': '20px'}),
            
            # Table 1
            dbc.Row([
                dbc.Col(
                    dbc.Table([
                        *[html.Tr([
                            html.Td(row[0], style={'border': '1px solid black', 'padding': '5px', 'width': '25%'}),
                            html.Td(row[1], style={'border': '1px solid black', 'padding': '5px', 'width': '25%', 'wordWrap': 'break-word'}),
                            html.Td(row[2], style={'border': '1px solid black', 'padding': '5px', 'width': '25%'}),
                            html.Td(row[3], style={'border': '1px solid black', 'padding': '5px', 'width': '25%'})
                        ]) for row in [
                            ["Site ID", select_site, "MME", "enBId"],
                            ["Site Name", "NEW BATUAMPAR", "MME In Pool", "59049"],
                            ["Type of Work", "EQP Upgrade Multisector LTE 900 10 MHz 2T2R (SECTOR 6)", "TAC", "11922"],
                            ["NE Type", "eNode B", "CI", "12,22,32,62"],
                            ["Band", "LTE 900", "PO Number", "4100005367"],
                            ["Connected User", "126", "IP eNB", "10.140.116.88"],
                            ["BW (Mhz)", "10", "RBS Type", "RBS 6201"],
                            ["City", "KOTA B A T A M-MC1", "", ""]
                        ]]
                    ], bordered=True, style={'width': '100%'}), width=12
                )
            ], style={'marginBottom': '20px'}),
            
            # Table 2
            dbc.Row([
                dbc.Col(
                    dbc.Table([
                        html.Tr([
                            html.Td("Integration date:", style={'border': '1px solid black', 'padding': '5px', 'backgroundColor': '#f2f2f2', 'width': '25%'}),
                            html.Td("20-Jun-24", style={'border': '1px solid black', 'padding': '5px', 'width': '25%'}),
                            html.Td("On-Air Date:", style={'border': '1px solid black', 'padding': '5px', 'backgroundColor': '#f2f2f2', 'width': '25%'}),
                            html.Td("20-Jun-24", style={'border': '1px solid black', 'padding': '5px', 'width': '25%'}),
                            html.Td("Acceptance date:", style={'border': '1px solid black', 'padding': '5px', 'backgroundColor': '#f2f2f2', 'width': '25%'}),
                            html.Td("", style={'border': '1px solid black', 'padding': '5px', 'width': '25%'})
                        ])
                    ], bordered=True, style={'width': '100%'}), width=12
                )
            ], style={'marginBottom': '20px'}),
            
            # Footer text
            dbc.Row([
                dbc.Col(html.P("This quality certificate is a legal note that Telkomsel's SQA department in regional office has approved the integration quality of mentioned type of work to the Telkomsel network and accepting reached KPI integration values.",
                               style={'textAlign': 'center', 'fontSize': '14px'}), width=12)
            ])
        ], fluid=True)
        return content_acc_page
    
    else:
        # Default content for other tabs
        return html.Div(f"Site: {select_site}, Band: {select_band}, Date Range: {start_date} to {end_date}")