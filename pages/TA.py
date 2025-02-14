import pyodbc
import pandas as pd
import numpy as np
import sqlalchemy
from sqlalchemy.engine import URL
from dash import Dash, dcc, html, Input, Output, callback, dash_table, State, dependencies, no_update, callback_context
from dash.dash_table.Format import Format, Scheme, Sign, Symbol
from collections import OrderedDict
import plotly.express as px
from datetime import date, datetime, timedelta
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
pd.options.mode.chained_assignment = None
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import dash
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
from database import uniq_siteta, query_ta

# Register page and external stylesheets
external_stylesheets = [dbc.themes.BOOTSTRAP]
dash.register_page(__name__, path='/ta')

# Load data

uniq_site = uniq_siteta('Site_id')
uniq_band = uniq_siteta('Band_id')
uniq_date = uniq_siteta('DATE_ID')


# Layout with responsive design using dbc.Container and dbc.Row
layout = dbc.Container(fluid=True, children=[
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                options=uniq_site,
                id='filter_Site',
                multi=True,
                placeholder="Pilih Site",
                clearable=True
            )
        ], width=12, lg=4),
        dbc.Col([
            dcc.Dropdown(
                options=uniq_band,
                id='filter_Band',
                multi=True,
                placeholder="Pilih Band",
                clearable=True
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
            dash_table.DataTable(
                id='datatableTA',
                columns=[{"name": i, "id": i, "selectable": True} for i in ['CELL', 'TA1', 'TA2', 'TA3', 'TA4', 'TA5', 'TA6', 'TA7', 'TA8']],
                editable=True,
                style_cell={'textAlign': 'center'},
                style_header={
                    'backgroundColor': 'blue',
                    'fontWeight': 'bold'
                },
                style_table={'width' : '60%'}
            )
        ], width=12)
    ], className="mb-3"),
    dbc.Row([
        dbc.Col(id='container', width=12)
    ]),
    dcc.Store(id="filter-df-store", data=None),
    dcc.Store(id="filter_Site-dropdown", data=None),
    dcc.Store(id="tabs", data=None)
])

# Callback to update the table
@callback(
    Output("datatableTA", "data"),
    Input("filter_Site", "value"),
    Input("filter_Band", "value"),
    Input("date_range", "value"),
    prevent_initial_call=True
)
def tabletanya(select_site, select_band, end_date):
    if not select_site or not select_band or not end_date:
        return None
    dfta = query_ta(select_site, select_band, end_date)
    dftatable = pd.DataFrame(dfta)
    end_date = pd.to_datetime(end_date)
    dftatablea = dftatable[['DATE_ID', 'label', 'Site_id', 'Band_id', 'TA_Index_m', 'Occurance']]
    
    dftatablea = dftatable.drop_duplicates(subset=['DATE_ID', 'label', 'Site_id', 'TA_Index_m', 'Occurance'])
    dftatablea = dftatablea.pivot(index=['DATE_ID', 'label', 'Site_id', 'Band_id'], columns='TA_Index_m', values='Occurance')
    dftatablea = dftatablea.rename_axis(['DATE_ID', 'label', 'Site_id', 'Band_id']).reset_index()

    data = dftatablea[
        (dftatablea['Site_id'].isin(select_site)) &
        (dftatablea['Band_id'].isin(select_band)) &
        (dftatablea['DATE_ID'].isin(end_date))
    ]
    data['CELL'] = data['label']
    data = data[['CELL', 'TA1', 'TA2', 'TA3', 'TA4', 'TA5', 'TA6', 'TA7', 'TA8']]
    data = pd.DataFrame([*data.values, ['Grand Total', *data.sum(numeric_only=True).values]], columns=data.columns)
    return data.to_dict('records')

# Callback to generate charts and tables
@callback(
    Output('container', 'children', allow_duplicate=True),
    Input('filter_Site', 'value'),
    Input('filter_Band', 'value'),
    Input('date_range', 'value'),
    prevent_initial_call=True
)
def chartandtable(select_site, select_band, end_date):
    if not select_site or not select_band or not end_date:
        return None
    dfta = query_ta(select_site, select_band, end_date)
    dftatable = pd.DataFrame(dfta)
    end_date = pd.to_datetime(end_date)
    dftatable = dftatable.drop_duplicates(subset=['DATE_ID', 'label', 'Site_id', 'Band_id', 'TA_Index_m', 'Occurance'])
    dftatablea = dftatable[['DATE_ID', 'label', 'Site_id', 'Band_id', 'TA_Index_m', 'Occurance']]
    dftatablea['CELL'] = dftatablea['label']
    dftatablea = dftatablea.drop_duplicates(subset=['DATE_ID', 'label', 'Site_id', 'Band_id', 'TA_Index_m', 'Occurance'])
    dftatablea = dftatablea.pivot(index=['DATE_ID', 'label', 'Site_id', 'Band_id'], columns='TA_Index_m', values='Occurance')
    dftatablea = dftatablea.rename_axis(['DATE_ID', 'label', 'Site_id', 'Band_id']).reset_index()

    dddf = dftatable[
        (dftatable['Site_id'].isin(select_site)) &
        (dftatable['Band_id'].isin(select_band)) &
        (dftatable['DATE_ID'].isin(end_date))
    ]
    try:
        cekcount = dddf['label'].unique()
        ceksek = len(cekcount)
    except IndexError:
        ceksek = 0

    if ceksek != 0:
        hasil = []
        for dfcount in range(ceksek):
            dfcel = dddf['label'].unique()[dfcount]
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            dffig = dddf[dddf['label'] == dfcel]
            fig = go.Figure(data=go.Bar(
                x=[tuple(dffig['TA_Index_m']), tuple(dffig['Distance_m'])],
                y=dffig['Occurance'],
                name="Total number of diners",
                marker=dict(color="paleturquoise")
            ))
            fig.add_trace(go.Scatter(
                x=[tuple(dffig['TA_Index_m']), tuple(dffig['Distance_m'])],
                y=dffig['Cumulative_Occurance'],
                yaxis="y2",
                name="Total bill amount",
                marker=dict(color="crimson")
            ))
            fig.update_layout(
                legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="left", x=0.32, title=None),
                font=dict(family="Courier", size=10, color="black"),
                yaxis=dict(showgrid=True, tickformat="..0f", side="left", range=[0, dffig['Occurance'].max() + (dffig['Occurance'].max() / 10)]),
                yaxis2=dict(showgrid=False, ticksuffix="%", side="right", overlaying="y", range=[0, 120], dtick=20, gridwidth=0.1, gridcolor='gray')
            )
            fig.update_layout(title_text=dfcel, title_x=0.5, title_y=1, margin={"l": 0, "r": 0, "b": 0, "t": 15}, title_font_color="black", showlegend=True, height=350, plot_bgcolor='white')
            fig.update_xaxes(showgrid=False, title=None, linecolor='black', ticklabelmode="period", tickangle=0)
            fig.update_yaxes(gridcolor='gray', gridwidth=0.5)

            grafik = dcc.Graph(figure=fig, style={"border": "2px black solid"})
            dffig['Cumulative_Occurance'] = dffig['Cumulative_Occurance'] / 100
            data = dffig[['TA_Index_m', 'Distance_m', 'Occurance', 'Cumulative_Occurance']].to_dict('records')

            tabel = dash_table.DataTable(
                style_cell={'textAlign': 'center'},
                style_data={'border': '1px solid black'},
                style_header={'border': '1px solid black'},
                style_header_conditional=[
                    {'if': {'header_index': 1}, 'fontWeight': 'bold', 'textAlign': 'center', 'backgroundColor': 'blue'},
                    {'if': {'header_index': 0}, 'fontWeight': 'bold', 'textAlign': 'center', 'backgroundColor': 'rgb(220, 220, 220)'}
                ],
                columns=[
                    {"name": ["CELL", 'TA Index'], 'id': 'TA_Index_m'},
                    {"name": [dfcel, 'Distance_m(m)'], 'id': 'Distance_m'},
                    {"name": [dfcel, 'Occurance (#)'], 'id': 'Occurance'},
                    {"name": [dfcel, 'Cumulative Occurance(%)'], 'id': 'Cumulative_Occurance', 'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.percentage)}
                ],
                data=data,
                merge_duplicate_headers=True
            )

            container = dbc.Row([
                dbc.Col([grafik], width=12, lg=6),
                dbc.Col([tabel], width=12, lg=6)
            ], className="mb-3")

            hasil.append(html.Div([container]))
        return hasil
    else:
        return ['', '']

# Callback to generate PDF
@callback(
    Output("download-pdf-from-ta", "data"),
    [Input("export-to-pdf", "n_clicks")],
    [
        State("url", "pathname"),
        State("filter_Site", "value"),
        State("filter_Band", "value"),
        State("date_range", "value"),
    ],
    prevent_initial_call=True
)
def generate_pdf_ta(n_clicks, pathname, select_site, select_band, end_date):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update
    if pathname != "/ta":
        return dash.no_update
    if pathname == '/ta' and n_clicks:
        try:
            if not select_site or not select_band or not end_date:
                return None
            dfta = query_ta(select_site, select_band, end_date)
            dftatable = pd.DataFrame(dfta)
            end_date = pd.to_datetime(end_date)
            dftatable = dftatable.drop_duplicates(subset=['DATE_ID', 'label', 'Site_id', 'Band_id', 'TA_Index_m', 'Occurance'])
            dftatablea = dftatable[['DATE_ID', 'label', 'Site_id', 'Band_id', 'TA_Index_m', 'Occurance']]
            dftatablea['CELL'] = dftatablea['label']
            dftatablea = dftatablea.drop_duplicates(subset=['DATE_ID', 'label', 'Site_id', 'Band_id', 'TA_Index_m', 'Occurance'])
            dftatablea = dftatablea.pivot(index=['DATE_ID', 'label', 'Site_id', 'Band_id'], columns='TA_Index_m', values='Occurance')
            dftatablea = dftatablea.rename_axis(['DATE_ID', 'label', 'Site_id', 'Band_id']).reset_index()
            # **Nama File PDF**
            pdf_filename = "table_output.pdf"
            pdf_path = os.path.join(os.getcwd(), pdf_filename)
            pdf = SimpleDocTemplate(pdf_filename, pagesize=(800, 1200))
            elements = []
            styles = getSampleStyleSheet()

            # **Folder untuk menyimpan gambar sementara**
            img_folder = "temp_images"
            if not os.path.exists(img_folder):
                os.makedirs(img_folder)

            # **Filter Data Sesuai Input**
            data = dftatablea[
                (dftatablea['Site_id'].isin(select_site)) &
                (dftatablea['Band_id'].isin(select_band)) &
                (dftatablea['DATE_ID'].isin(end_date))
            ]
            df_len = (data['label'].str.len()).max()
            data['CELL'] = data['label']
            data = data[['CELL', 'TA1', 'TA2', 'TA3', 'TA4', 'TA5', 'TA6', 'TA7', 'TA8']]
            data = pd.DataFrame(
                [*data.values, ['Grand Total', *data.sum(numeric_only=True).values]],
                columns=data.columns
            )

            # **Buat Tabel Utama**
            table_data = [data.columns] + data.values.tolist()
            table_atas = Table(table_data, colWidths=[80] + [40] * (len(data.columns) - 1))
            table_atas.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.blue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ]))

            table_atas_layout = Table(
                [[table_atas]],
                hAlign='LEFT'
            )
            table_atas_layout.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ]))

            ad_zero = ''
            table_atas_ad_zero_layout = Table(
                [[table_atas_layout, ad_zero]],
                colWidths=[420, 360]
            )
            table_atas_ad_zero_layout.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ]))

            elements.append(table_atas_ad_zero_layout)
            elements.append(Spacer(1, 5))

            # **Loop untuk setiap label**
            dddf = dftatable[
                (dftatable['Site_id'].isin(select_site)) &
                (dftatable['Band_id'].isin(select_band)) &
                (dftatable['DATE_ID'].isin(end_date))
            ]
            unique_labels = dddf['label'].unique()
            for label in unique_labels:
                dffig = dddf[dddf['label'] == label]

                # **Buat Grafik**
                fig = go.Figure()
                fig = go.Figure(data=go.Bar(
                    x=[tuple(dffig['TA_Index_m']), tuple(dffig['Distance_m'])],
                    y=dffig['Occurance'],
                    name="Total number of diners",
                    marker=dict(color="paleturquoise")
                ))
                fig.add_trace(go.Scatter(
                    x=[tuple(dffig['TA_Index_m']), tuple(dffig['Distance_m'])],
                    y=dffig['Cumulative_Occurance'],
                    yaxis="y2",
                    name="Total bill amount",
                    marker=dict(color="crimson")
                ))
                fig.update_layout(
                    legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="left", x=0.28, title=None),
                    font=dict(family="Courier", size=10, color="black"),
                    yaxis=dict(showgrid=True, tickformat=".0f", side="left", range=[0, dffig['Occurance'].max() + (dffig['Occurance'].max() / 10)]),
                    yaxis2=dict(showgrid=False, ticksuffix="%", side="right", overlaying="y", range=[0, 120], dtick=20, gridwidth=0.1, gridcolor='gray')
                )
                fig.update_layout(title_text=label, title_x=0.5, title_y=1, margin={"l": 0, "r": 0, "b": 0, "t": 15}, title_font_color="black", showlegend=True, height=350, plot_bgcolor='white')
                fig.update_xaxes(showgrid=False, title=None, linecolor='black', ticklabelmode="period", tickangle=0)
                fig.update_yaxes(gridcolor='gray', gridwidth=0.5)

                img_bytes = io.BytesIO()
                fig.write_image(img_bytes, format="png", scale=2)
                img_bytes.seek(0)
                chart_with_border = Table(
                    [[Image(img_bytes, width=370, height=180)]],
                    colWidths=[390],
                    hAlign='LEFT'
                )
                chart_with_border.setStyle(TableStyle([
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ]))

                # **Buat Tabel untuk label**
                data_fig = (dffig[['TA_Index_m', 'Distance_m', 'Occurance', 'Cumulative_Occurance']])
                #data_fig['Cumulative_Occurance'] = (data_fig['Cumulative_Occurance'] / 100).apply(lambda x: f"{x:.2%}")
                table_data = [
                    ["CELL", label, "", ""],
                    ["TA Index", "Distance_m (m)", "Occurance (#)", "Cumulative Occurance (%)"],
                ]
                for index, row in data_fig.iterrows():
                    table_data.append(row.tolist())

                table_loop = Table(table_data, style=[
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("BACKGROUND", (0, 1), (-1, 1), colors.blue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("SPAN", (1, 0), (3, 0)),
                    ("BACKGROUND", (0, 1), (-1, 1), colors.blue),
                    ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                    ("FONTNAME", (0, 2), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("FONTSIZE", (0, 1), (-1, 1), 10),
                    ("FONTSIZE", (0, 2), (-1, -1), 10),
                    ("BACKGROUND", (0, 2), (-1, -1), colors.whitesmoke),
                ])

                # **Gabungkan Chart dan Tabel secara Horizontal**
                chart_table_layout = Table(
                    [[chart_with_border, table_loop]],
                    colWidths=[400, 360]
                )
                chart_table_layout.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ]))

                elements.append(chart_table_layout)
                elements.append(Spacer(1, 5))

            # **Buat PDF**
            pdf.build(elements)

            # **Return DCC Download Component**
            return dcc.send_file(pdf_filename)
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None
    return None