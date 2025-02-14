import folium
from urllib.request import urlopen
import plotly.graph_objects as go
import pandas as pd
from dash import Dash, dcc, html, Input, Output, callback, State, dependencies, no_update, callback_context
import plotly.express as px
import numpy as np
from datetime import date, datetime, timedelta
import configparser
import os, glob
import base64
import dash
from fpdf import FPDF
import io
import dash_bootstrap_components as dbc
from database import uniq_sitemdt, query_mdt

# Decode token and style
token = base64.b64decode(b'cGsuZXlKMUlqb2ljSFZ5Ym05dGJ6RXhJaXdpWVNJNkltTnROR0pwYVdNMmN6QXdiakl5YlhNNWNHc3hhSEJwTm1jaWZRLjRuYUdPQWNrajJoZ0hGMmFVSEZGdWc=').decode('utf-8')
stylemcomandmap = base64.b64decode(b'bWFwYm94Oi8vc3R5bGVzL3B1cm5vbW8xMS9jbTRpanloc3gwMDZkMDFyMGcycmQ0d2hv').decode('utf-8')
"""
# Load data
path_mdt_ori = 'C:\\Users\\Purnomo\\Downloads\\'
path_mdt_apend = 'D:\\MDT\\'


MDT['date'] = MDT['date'].astype('string')
MDT['site'] = np.where((MDT['site'].str[1:2] == '_') | (MDT['site'].str[1:2] == '-'), MDT['site'].str[2:8], MDT['site'].str[0:6])
MDT['CI_ID'] = MDT['ci'].astype(str)

# Define Band logic
MDT['Band'] = np.where(
    MDT['ci'] <= 100,
    np.where(MDT['ci'].astype(int).astype(str).str[-1] == '1', 'L1800',
             np.where(MDT['ci'].astype(int).astype(str).str[-1] == '2', 'L900',
                      np.where(MDT['ci'].astype(int).astype(str).str[-1] == '3', 'L2100',
                               np.where(MDT['ci'].astype(int).astype(str).str[-1] == '4', 'L2300',
                                        np.where(MDT['ci'].astype(int).astype(str).str[-1] == '5', 'L2300',
                                                 np.where(MDT['ci'].astype(int).astype(str).str[-1] == '6', 'L2300', 'CEK')))))),
    np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '114', 'L2300',
             np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '124', 'L2300',
                      np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '134', 'L2300',
                               np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '115', 'L2300',
                                        np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '141', 'L1800',
                                                 np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '143', 'L2100',
                                                          np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '115', 'L2300',
                                                                   np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '125', 'L2300',
                                                                            np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '135', 'L2300',
                                                                                     np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '145', 'L2300',
                                                                                              np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '155', 'L2300',
                                                                                                       np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '165', 'L2300',
                                                                                                                np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '202', 'L900',
                                                                                                                         np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '212', 'L900',
                                                                                                                                  np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '222', 'L900',
                                                                                                                                           np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '241', 'L1800',
                                                                                                                                                    np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '161', 'L1800',
                                                                                                                                                             np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '171', 'L1800',
                                                                                                                                                                      np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '181', 'L1800',
                                                                                                                                                                               np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '111', 'L1800',
                                                                                                                                                                                        np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '121', 'L1800',
                                                                                                                                                                                                 np.where(MDT['ci'].astype(int).astype(str).str[0:3] == '131', 'L1800', 'CEK')))))))))))))))))))))))
"""
uniq_site = uniq_sitemdt('SITEID')
uniq_band = uniq_sitemdt('Band')
uniq_date = uniq_sitemdt('date')
# Register page
dash.register_page(__name__, path='/mdt')

# Hidden stores
filter_site_store = dcc.Store(id='filter-site-value', data=None)
filter_Band_store = dcc.Store(id='filter_Band-value', data=None)
filter_date_store = dcc.Store(id='filter-date-mdt-value', data=None)
filter_Site_dropdown = dcc.Store(id='filter_Site-dropdown', data=None)
filter_df_store = dcc.Store(id='filter-df-store', data=None)

# Layout with dbc.Container, dbc.Row, and dbc.Col
layout = dbc.Container(fluid=True, children=[
    dbc.Row([
        dbc.Col([
            filter_site_store,
            filter_Band_store,
            filter_date_store,
            filter_Site_dropdown,
            filter_df_store,
            dcc.Store(id="tabs", data=None),
            html.Div("Created by: Purnomo Aji | Email: aji.purnomo.uin@gmail.com | WA: 082160261391",
                     style={'color': 'blue', 'fontSize': 8, 'textAlign': 'center'})
        ], width=12),
    ], className="mb-3"),
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                options=uniq_site,
                id='filter_Site',
                multi=True,
                placeholder="Pilih Site",
                clearable=True,
            )
        ], width=12, lg=4),
        dbc.Col([
            dcc.Dropdown(
                options=uniq_band,
                id='filter_Band',
                multi=True,
                placeholder="Pilih band",
                clearable=True,
            )
        ], width=12, lg=4),
        dbc.Col([
            dcc.Dropdown(
                options=[{'label': date, 'value': date} for date in uniq_date],
                id="date_range",
                multi=True,
                placeholder="Pilih date",
                clearable=True,
            )
        ], width=12, lg=4),
    ], className="mb-3"),
    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id='map-mdt',
                style={'height': '500px'}
            )
        ], width=12),
    ], className="mb-3"),
])

# Callback to update the map
@callback(
    Output("map-mdt", "figure"),
    Input("filter_Site", "value"),
    Input("filter_Band", "value"),
    Input("date_range", "value"),
    prevent_initial_call=True
)
def update_bar_chart(select_site, select_band, select_date):
    if not select_site or not select_band or not select_date:
        return go.Figure()
    if select_site or select_date:
        dfdata = query_mdt(select_site, select_date)
        filtered_data = pd.DataFrame(dfdata)
    filtered_data = filtered_data[filtered_data['Band'].isin(select_band)]
    filtered_data['lat_grid'] = pd.to_numeric(filtered_data['lat_grid'], errors='coerce')
    filtered_data['long_grid'] = pd.to_numeric(filtered_data['long_grid'], errors='coerce')
    filtered_data['ci'] = filtered_data['ci'].astype(str)
    filtered_data= filtered_data.sort_values(by=['SITEID', 'ci'], ascending=True)
    
    fig = px.scatter_mapbox(
        filtered_data,
        lat="lat_grid",
        lon="long_grid",
        hover_name="SITEID",
        hover_data=['ci'],
        zoom=14,
        color="ci"
    )
    fig.update_layout(
        mapbox_style=stylemcomandmap,
        mapbox_accesstoken=token,
        title_x=0.5,
        title_y=1,
        title_text=f"MDT_{select_site}_{select_band}",
        margin={"l": 0, "r": 0, "b": 0, "t": 15},
        title_font_color="red",
        showlegend=True,
        height=520,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.001, title='ci')
    )
    return fig

# Callbacks for hidden stores
@callback(
    Output("filter-site-value", "data"),
    [Input("filter_Site", "value")]
)
def get_filter_site_value(value):
    return value

@callback(
    Output("filter_Band-value", "data"),
    [Input("filter_Band", "value")],
    prevent_initial_call=True
)
def get_filter_Band_value(value):
    return value

@callback(
    Output("filter-date-mdt-value", "data"),
    [Input("date_range", "value")]
)
def get_filter_date_range_value(value):
    return value

# Callback to generate PDF
@callback(
    Output("download-pdf", "data"),
    [Input("export-to-pdf", "n_clicks")],
    [
        State("url", "pathname"),
        State("filter_Site", "value"),
        State("filter_Band", "value"),
        State("date_range", "value"),
    ],
    prevent_initial_call=True
)
def generate_pdf_mdt(n_clicks, pathname, select_site, select_band, select_date):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update
    if pathname != "/mdt":
        return dash.no_update
    if pathname == '/mdt' and n_clicks:
        if not select_site or not select_band or not select_date:
            return None
        try:
            # Generate figure
            dfdata = query_mdt(select_site, select_date)
            filtered_data = pd.DataFrame(dfdata)
            filtered_data = filtered_data[filtered_data['Band'].isin(select_band)]

            fig = px.scatter_mapbox(
                filtered_data,
                lat="lat_grid",
                lon="long_grid",
                hover_name="SITEID",
                hover_data=['ci'],
                zoom=14,
                color="ci"
            )
            fig.update_layout(
                mapbox_style=stylemcomandmap,
                mapbox_accesstoken=token,
                title_x=0.5,
                title_y=1,
                title_text=f"MDT_{select_site}_{select_band}",
                margin={"l": 0, "r": 0, "b": 0, "t": 15},
                title_font_color="red",
                showlegend=True,
                height=520,
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.001, title='ci')
            )

            # Save the figure to a BytesIO buffer as an image
            img_buffer = io.BytesIO()
            fig.write_image(img_buffer, format="png")
            img_buffer.seek(0)

            # Generate PDF using FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="MDT Map", ln=True, align='C')
            pdf.image(img_buffer, x=10, y=10, w=200, type="PNG")
            pdf_buffer = io.BytesIO()
            pdf.output(pdf_buffer)
            pdf_buffer.seek(0)

            return dcc.send_bytes(pdf_buffer.getvalue(), "MDT_Report.pdf")
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None
    return None