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
from database import konek_sql_server, uniq_sitehourly4g, query_ta
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

dash.register_page(__name__, path='/report/report-balancing')

# Konfigurasi Google Sheets
spreadsheet_id = "16vr_xg5ADdlqELqdAu8bcBuk1YKTBZsO60ai0OdNwv8"
sheet_id = "0"
url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?gid={sheet_id}&format=csv"

def dfgsheet():
    return pd.read_csv(url, header=1)

def site_balancing():
    return dfgsheet()['SiteID'].tolist()

def get_filtered_sites(pic=None):
    df = dfgsheet()
    # Filter dasar
    filtered_df = df[
        (df['Connected Status'] == 'Connected') &
        (df['Status'] != '1. QC Pass Sign') &
        (df['Status'] != '1. QC Pass Sign M-QC')
    ]
    # Jika PIC diberikan, tambahkan filter berdasarkan PIC
    if pic:
        filtered_df = filtered_df[filtered_df['PIC Optim'] == pic]
    return filtered_df['SiteID'].unique().tolist()

# Data SITEID dan DATE_ID
site_ids = uniq_sitehourly4g('SITEID')
date_ids = uniq_sitehourly4g('DATE_ID')

# Layout Utama
layout = dbc.Container(fluid=True, children=[
    dcc.Store(id='filter-df-store', data=[]),
    
    # Tabs for navigation
    dbc.Row([
        dbc.Col([
            dcc.Tabs(id="tabs", value='filter', children=[
                dcc.Tab(label='Filter', value='filter')
            ]),
        ], width=12),
    ], className="mb-3"),
    
    # Filter Section
    dbc.Row(id="filter_dropdown_balancing", children=[
        dbc.Col([
            dcc.Dropdown(
                id="filter_Site",
                options=[
                    {"label": site, "value": site} for site in site_ids
                ] + [
                    {"label": "KPI_OG", "value": "site_balancing"},
                    {"label": "List_site_Ardyan", "value": "site_ardyan"},
                    {"label": "List_site_Purnomo", "value": "site_purnomo"}
                ],
                placeholder="Pilih Site",
                multi=True,
                style={"width": "100%"},
            ),
        ], width=12, lg=6),
        dbc.Col([
            dcc.DatePickerRange(
                id="date_range",
                min_date_allowed=min(date_ids),
                max_date_allowed=max(date_ids),
                start_date=(max(date_ids) - timedelta(days=10)),
                end_date=max(date_ids),
                style={"width": "100%"},
            ),
        ], width=12, lg=6),
    ], className="mb-3"),
    
    # Content Section
    dbc.Row([
        dbc.Col(id="tabs_content", width=12),
    ]),
])



# Callback to toggle filter section visibility
@callback(
    Output("filter_dropdown_balancing", "style", allow_duplicate=True),
    Input("tabs", "value"),
    prevent_initial_call=True
)
def toggle_filter_section(tab):
    if tab != "filter":
        return {'display': 'none'}

# Callback untuk Memperbarui Tabs
@callback(
    Output("tabs", "children", allow_duplicate=True),
    Input("filter_Site", "value"),
    prevent_initial_call=True
)
def update_tabs(slect_site):
    tabs = [dcc.Tab(label='Filter', value='filter')]
    if slect_site:
        if "site_balancing" in slect_site:
            slect_site.remove("site_balancing")
            slect_site.extend(get_filtered_sites())  # Tanpa filter PIC
        elif "site_ardyan" in slect_site:
            slect_site.remove("site_ardyan")
            slect_site.extend(get_filtered_sites(pic="Ardiyan"))
        elif "site_purnomo" in slect_site:
            slect_site.remove("site_purnomo")
            slect_site.extend(get_filtered_sites(pic="Purnomo"))
        tabs.extend([dcc.Tab(label=site, value=site) for site in slect_site])
    return tabs

# Callback untuk Query Data
@callback(
    Output('filter-df-store', 'data', allow_duplicate=True),
    Input("tabs", "value"),
    Input("filter_Site", "value"),
    Input("date_range", "start_date"),
    Input("date_range", "end_date"),
    prevent_initial_call=True
)
def query_data(tab, slect_site, start_date, end_date):
    if tab != 'filter' or not slect_site or not start_date or not end_date:
        return no_update
    try:
        engine = konek_sql_server()
        sites = set(slect_site) if slect_site else set()
        if "site_balancing" in sites:
            sites.remove("site_balancing")
            sites.update(get_filtered_sites())  # Tanpa filter PIC
        elif "site_ardyan" in sites:
            sites.remove("site_ardyan")
            sites.update(get_filtered_sites(pic="Ardiyan"))
        elif "site_purnomo" in sites:
            sites.remove("site_purnomo")
            sites.update(get_filtered_sites(pic="Purnomo"))
        site_filter = ', '.join(map(lambda x: f"'{x}'", set(sites)))
        query = f"""
        SELECT DISTINCT DATE_ID, hour_id, NEID, Band, SITEID, Sector_gabung, EUtranCellFDD,
        Active_User, DL_Resource_Block_Utilizing_Rate
        FROM dbo.hourly4g
        WHERE DATE_ID BETWEEN '{start_date}' AND '{end_date}'
        AND SITEID IN ({site_filter})
        ORDER BY DATE_ID, hour_id ASC;
        """
        hourly4g = pd.read_sql_query(query, engine)
        hourly4g['SECTOR'] = 'Sector ' + hourly4g['Sector_gabung'].astype(str)
        engine.dispose()
        return hourly4g.to_dict('records')
    except Exception as e:
        print(f"Error executing query: {e}")
        return no_update

# Helper Function untuk Membuat Grafik
def create_chart_render_content(data, title, y_column):
    return dcc.Graph(
        figure=go.Figure(
            data=[
                go.Scatter(
                    x=[tuple(df_label['DATE_ID']), tuple(df_label['hour_id'])],
                    y=df_label[y_column],
                    name=label,
                    mode='lines',
                    marker=dict()
                )
                for label, df_label in data.groupby('label')
            ],
            layout=go.Layout(
                title=title,
                plot_bgcolor='white',
                title_x=0.5,
                title_y=1,
                margin={"l": 2, "r": 2, "b": 2, "t": 15},
                title_font_color="black",
                height=250,
                paper_bgcolor='rgba(255,255,255,1)',
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.45,
                    xanchor="left",
                    x=0.001,
                    title=None
                ),
                font=dict(family="Courier", size=10, color="black"),
                xaxis=dict(showgrid=False, gridcolor='lightgrey', linewidth=2, linecolor='black', tickangle=45),
                yaxis=dict(gridcolor='lightgrey', linewidth=2, linecolor='black')
            )
        ),
        style={"border": "2px black solid", "width": "100%", "margin": "2px"}
    )

# Callback untuk Render Konten Tab
@callback(
    Output("tabs_content", "children", allow_duplicate=True),
    [
        Input("tabs", "value"),
        State("filter-df-store", "data"),
        Input("filter_Site", "value"),
        Input("date_range", "end_date"),
    ],
    prevent_initial_call=True
)
def render_content(tab, df_store, slect_site, end_date):
    if tab == 'filter':
        if not slect_site:
            return html.Div("Pilih site dan tanggal untuk melihat konten")
        sites = set(slect_site) if slect_site else set()
        if "site_balancing" in sites:
            sites.remove("site_balancing")
            sites.update(get_filtered_sites())  # Tanpa filter PIC
        elif "site_ardyan" in sites:
            sites.remove("site_ardyan")
            sites.update(get_filtered_sites(pic="Ardiyan"))
        elif "site_purnomo" in sites:
            sites.remove("site_purnomo")
            sites.update(get_filtered_sites(pic="Purnomo"))
        site_filter = sorted(set(sites))
        df_sheet = dfgsheet()
        if isinstance(df_sheet, pd.DataFrame) and 'SiteID' in df_sheet.columns:
            df_sheet = df_sheet[['SiteID', 'NEID', 'Connected/ Implement Date', 'Sector Activity', 'Plan DT', 'Actual Drive Test', 'PIC Optim', 'Updated Plan Submit QC', 'Status']]
            df_sheet = df_sheet[(df_sheet['Status'] != '1. QC Pass Sign') & (df_sheet['Status'] != '1. QC Pass Sign M-QC')]
            df_table_balance_in_filter = df_sheet[df_sheet['SiteID'].isin(site_filter)].to_dict('records')
        else:
            df_table_balance_in_filter = []
        if not df_table_balance_in_filter:
            return html.Div("Data balancing tidak ada, Pilih tab untuk melihat konten")
        tabel_balance_in_filter = dash_table.DataTable(
            style_cell={'textAlign': 'center'},
            style_data={'border': '1px solid black'},
            style_header={'border': '1px solid black'},
            style_header_conditional=[
                {'if': {'header_index': 0}, 'fontWeight': 'bold', 'textAlign': 'center', 'backgroundColor': 'blue'},
                {'if': {'header_index': 0}, 'fontWeight': 'bold', 'textAlign': 'center', 'backgroundColor': 'rgb(220, 220, 220)'}
            ],
            columns=[{"name": colbalance, "id": colbalance, "selectable": True} for colbalance in df_table_balance_in_filter[0].keys()],
            data=df_table_balance_in_filter,
            merge_duplicate_headers=True
        )
        
        content = [
            dbc.Row([
                dbc.Col(tabel_balance_in_filter, width=12),
            ], className="mb-3"),
        ]
    elif tab != 'filter':
        if df_store:
            slect_site = [tab]
            select_date = [datetime.strptime((end_date.split('T')[0]), '%Y-%m-%d')]
            if select_date[0].date() == date.today():
                select_date = [datetime.strptime((end_date.split('T')[0]), '%Y-%m-%d') - timedelta(days=1)]
            else:
                select_date = [end_date]
            select_band = 'L1800'
            df_ta = query_ta(slect_site, select_band, select_date)
            hourly4g = pd.DataFrame(df_store)
            if not hourly4g.empty and 'SITEID' in hourly4g.columns:
                hourly4g = hourly4g[hourly4g['SITEID'] == tab]
                if not hourly4g.empty:
                    try:
                        hourly4g['label'] = hourly4g['NEID'].str[-2:] + hourly4g['EUtranCellFDD'].str[-1:]
                        hourly4g['sector_multi'] = 'Sector ' + hourly4g['EUtranCellFDD'].str[-1:]
                        hourly4g['DATE_ID'] = pd.to_datetime(hourly4g['DATE_ID'], errors='coerce').dt.strftime('%d-%b')
                        hourly4g['hour_id'] = hourly4g['hour_id'].astype(str).str.zfill(2)
                        sectors = ['Sector 1', 'Sector 2', 'Sector 3']
                        df_sheet = dfgsheet()
                        if isinstance(df_sheet, pd.DataFrame) and 'SiteID' in df_sheet.columns:
                            df_sheet = df_sheet[['SiteID', 'NEID', 'Connected/ Implement Date', 'Sector Activity', 'Plan DT', 'Actual Drive Test', 'PIC Optim', 'Updated Plan Submit QC', 'Status']]
                            df_sheet = df_sheet[(df_sheet['Status'] != '1. QC Pass Sign') & (df_sheet['Status'] != '1. QC Pass Sign M-QC')]
                            df_table_balance_in_filter = df_sheet[df_sheet['SiteID'] == tab].to_dict('records')
                        else:
                            df_table_balance_in_filter = []
                        tabel_balance = dash_table.DataTable(
                            style_cell={'textAlign': 'center'},
                            style_data={'border': '1px solid black'},
                            style_header={'border': '1px solid black'},
                            style_header_conditional=[
                                {'if': {'header_index': 0}, 'fontWeight': 'bold', 'textAlign': 'center', 'backgroundColor': 'blue'},
                                {'if': {'header_index': 0}, 'fontWeight': 'bold', 'textAlign': 'center', 'backgroundColor': 'rgb(220, 220, 220)'}
                            ],
                            columns=[{"name": colbalance, "id": colbalance, "selectable": True} for colbalance in df_table_balance_in_filter[0].keys()],
                            data=df_table_balance_in_filter,
                            merge_duplicate_headers=True
                        )

                        # Chart PRB
                        chart_prb = [
                            create_chart_render_content(hourly4g[hourly4g['SECTOR'] == sector], f"PRB {sector}", 'DL_Resource_Block_Utilizing_Rate')
                            for sector in sectors
                        ]

                        # Chart AU
                        chart_au = [
                            create_chart_render_content(hourly4g[hourly4g['SECTOR'] == sector], f"AU {sector}", 'Active_User')
                            for sector in sectors
                        ]

                        # Chart PRB TDD
                        chart__prb_tdd = [
                            create_chart_render_content(
                                hourly4g[(hourly4g['SECTOR'] == sector) & (hourly4g['Band'] == 'L2300')],
                                f"PRB TDD Only {sector}",
                                'DL_Resource_Block_Utilizing_Rate'
                            ) if len(hourly4g[(hourly4g['SECTOR'] == sector) & (hourly4g['Band'] == 'L2300')]) > 0 else
                            dcc.Graph(
                                figure=go.Figure(
                                    layout=go.Layout(
                                        plot_bgcolor='white',
                                        paper_bgcolor='white',
                                        margin={"l": 0, "r": 0, "b": 0, "t": 0},
                                        height=250,
                                        showlegend=False,
                                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                                    )
                                ),
                            style={"width": "100%", "margin": "2px"}
                            )
                            for sector in sectors
                        ]

                        # Chart AU TDD
                        chart__au_tdd = [
                            create_chart_render_content(
                                hourly4g[(hourly4g['SECTOR'] == sector) & (hourly4g['Band'] == 'L2300')],
                                f"AU TDD Only {sector}",
                                'Active_User'
                            ) if len(hourly4g[(hourly4g['SECTOR'] == sector) & (hourly4g['Band'] == 'L2300')]) > 0 else
                            dcc.Graph(
                                figure=go.Figure(
                                    layout=go.Layout(
                                        plot_bgcolor='white',
                                        paper_bgcolor='white',
                                        margin={"l": 0, "r": 0, "b": 0, "t": 0},
                                        height=250,
                                        showlegend=False,
                                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                                    )
                                ),
                                style={"width": "100%", "margin": "2px"}
                            )
                            for sector in sectors
                        ]

                        if len(hourly4g[hourly4g['Band'] == 'L2300']) > 0:
                            content = [
                                dbc.Row([
                                    dbc.Col(tabel_balance, width=12)
                                ], className="mb-2"),
                                dbc.Row([
                                    dbc.Col(chart, width=4) for chart in chart_prb
                                ], className="mb-2"),
                                dbc.Row([
                                    dbc.Col(chart, width=4) for chart in chart_au
                                ], className="mb-2"),
                                dbc.Row([
                                    dbc.Col(chart, width=4) for chart in chart__prb_tdd
                                ], className="mb-2"),
                                dbc.Row([
                                    dbc.Col(chart, width=4) for chart in chart__au_tdd
                                ], className="mb-2"),
                            ]
                        else:
                            content = [
                                dbc.Row([
                                    dbc.Col(tabel_balance, width=12)
                                ], className="mb-2"),
                                dbc.Row([
                                    dbc.Col(chart, width=4) for chart in chart_prb
                                ], className="mb-2"),
                                dbc.Row([
                                    dbc.Col(chart, width=4) for chart in chart_au
                                ], className="mb-2"),
                            ]

                    except Exception as e:
                        print(f"Error: {e}")
                        return html.Div('Site dan date yang anda masukan tidak ada, silahkan pilih site dan date yang lain')
        elif not df_store:
            content = []
    return html.Div(content)


# Helper Function untuk Membuat Grafik
def create_chart_export(data, title, y_column):
        fig = go.Figure(
            data=[
                go.Scatter(
                    x=[tuple(df_label['DATE_ID']), tuple(df_label['hour_id'])],
                    y=df_label[y_column],
                    name=label,
                    mode='lines',
                    marker=dict()
                )
                for label, df_label in data.groupby('label')
            ],
            layout=go.Layout(
                title=title,
                plot_bgcolor='white',
                title_x=0.5,
                title_y=1,
                margin={"l": 2, "r": 2, "b": 2, "t": 15},
                title_font_color="black",
                height=250,
                paper_bgcolor='rgba(255,255,255,1)',
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.45,
                    xanchor="left",
                    x=0.001,
                    title=None
                ),
                font=dict(family="Courier", size=10, color="black"),
                xaxis=dict(showgrid=False, gridcolor='lightgrey', linewidth=2, linecolor='black', tickangle=45),
                yaxis=dict(gridcolor='lightgrey', linewidth=2, linecolor='black')
            )
        )
        return fig

# Callback untuk Generate PDF
@callback(
    Output("download-pdf-from-balancing", "data", allow_duplicate=True),
    [Input("export-to-pdf", "n_clicks")],
    [
        State("url", "pathname"),
        State("filter-df-store", "data"),
        Input("filter_Site", "value")
    ],
    prevent_initial_call=True
)
def generate_pdf_balancing(n_clicks, pathname, df_store, slect_site):
    if pathname != "/report/report-balancing":
        return dash.no_update

    if pathname == '/report/report-balancing' and n_clicks:
        pdf_filename = "Report_Balancing.pdf"
        pdf_path = os.path.join(os.getcwd(), pdf_filename)
        pdf = SimpleDocTemplate(pdf_filename, pagesize=(800, 1200))
        elements = []
        styles = getSampleStyleSheet()

        sites = set(slect_site) if slect_site else set()
        if "site_balancing" in sites:
            sites.remove("site_balancing")
            sites.update(get_filtered_sites())  # Tanpa filter PIC
        elif "site_ardyan" in sites:
            sites.remove("site_ardyan")
            sites.update(get_filtered_sites(pic="Ardiyan"))
        elif "site_purnomo" in sites:
            sites.remove("site_purnomo")
            sites.update(get_filtered_sites(pic="Purnomo"))
        site_filter = sorted(set(sites))
        df_sheet = dfgsheet()
        if isinstance(df_sheet, pd.DataFrame) and 'Site' in df_sheet.columns:
            df_table_balance_in_filter = df_sheet[df_sheet['Site'].isin(site_filter)].to_dict('records')
        else:
            df_table_balance_in_filter = []

        pdf_table_balance = pd.DataFrame(df_table_balance_in_filter)
        df_pdf_table_balance = [pdf_table_balance.columns] + pdf_table_balance.values.tolist()
        pdf_table_balance_atas = Table(df_pdf_table_balance, style=[
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 2), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 2), (-1, -1), 8),
            ("BACKGROUND", (0, 2), (-1, -1), colors.whitesmoke),
            ])
        table_blank_atas = ''
        pdf_table_balance_atas_layout = Table(
                    [[pdf_table_balance_atas, table_blank_atas]],
                    colWidths=[400, 360]
                )
        pdf_table_balance_atas_layout.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ]))
        elements.append(pdf_table_balance_atas_layout)
        elements.append(Spacer(1, 5))

        hourly4g = pd.DataFrame(df_store)
        if hourly4g.empty or 'SITEID' not in hourly4g.columns:
            return dash.no_update

        for site_list_balancing in site_filter:
            hourly4g_balancing = hourly4g[hourly4g['SITEID'] == site_list_balancing]
            hourly4g_balancing['label'] = hourly4g_balancing['NEID'].str[-2:] + hourly4g_balancing['EUtranCellFDD'].str[-1:]
            hourly4g_balancing['sector_multi'] = 'Sector ' + hourly4g_balancing['EUtranCellFDD'].str[-1:]
            hourly4g_balancing['DATE_ID'] = pd.to_datetime(hourly4g_balancing['DATE_ID'], errors='coerce').dt.strftime('%d-%b')
            hourly4g_balancing['hour_id'] = hourly4g_balancing['hour_id'].astype(str).str.zfill(2)
            sectors = ['Sector 1', 'Sector 2', 'Sector 3']
            df_table_balancing = df_sheet[df_sheet['SiteID'] == site_list_balancing]
            df_table_balancing_in_for = [df_table_balancing.columns] + df_table_balancing.values.tolist()

            table_balancing_in_for = Table(df_table_balancing_in_for, style=[
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 2), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("FONTSIZE", (0, 2), (-1, -1), 10),
                ("BACKGROUND", (0, 2), (-1, -1), colors.whitesmoke),
                ])
            table_blank_atas = ''
            table_balancing_in_for_layout = Table(
                [[table_balancing_in_for, table_blank_atas]],
                colWidths=[400, 360]
                )
            table_balancing_in_for_layout.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ]))
            elements.append(table_balancing_in_for_layout)
            elements.append(Spacer(1, 5))
        
            prb_images = []
            au_images = []
            prb_tdd_images = []
            au_tdd_images = []

            for sector in sectors:
                chart_prb = create_chart_export(hourly4g_balancing[hourly4g_balancing['SECTOR'] == sector], f"PRB {sector}", 'DL_Resource_Block_Utilizing_Rate')
                img_bytes_chart_prb = io.BytesIO()
                chart_prb.write_image(img_bytes_chart_prb, format="png", scale=2)
                img_bytes_chart_prb.seek(0)

                chart_table_prb = Table([[Image(img_bytes_chart_prb, width=200, height=130)]], colWidths=220)
                chart_table_prb.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1, 'red'),  # Garis grid 1px warna hitam
                ]))
                prb_images.append(chart_table_prb)
                prb_images.append(Spacer(1, 5))

                chart_au = create_chart_export(hourly4g_balancing[hourly4g_balancing['SECTOR'] == sector], f"AU {sector}", 'Active_User')
                img_bytes_chart_au = io.BytesIO()
                chart_au.write_image(img_bytes_chart_au, format="png", scale=2)
                img_bytes_chart_au.seek(0)

                chart_table_au = Table([[Image(img_bytes_chart_au, width=200, height=130)]], colWidths=220)
                chart_table_au.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1, 'black'),  # Garis grid 1px warna hitam
                ]))
                au_images.append(chart_table_au)
                au_images.append(Spacer(1, 5))

                if 'L2300' in hourly4g_balancing['Band'].values:
                    chart_prb_tdd = create_chart_export(hourly4g_balancing[(hourly4g_balancing['SECTOR'] == sector) & (hourly4g_balancing['Band'] == 'L2300')],
                                                 f"PRB TDD {sector}", 'DL_Resource_Block_Utilizing_Rate')
                    img_bytes_chart_prb_tdd = io.BytesIO()
                    chart_prb_tdd.write_image(img_bytes_chart_prb_tdd, format="png", scale=2)
                    img_bytes_chart_prb_tdd.seek(0)

                    chart_table_prb_tdd = Table([[Image(img_bytes_chart_prb_tdd, width=200, height=130)]], colWidths=220)
                    chart_table_prb_tdd.setStyle(TableStyle([
                        ('GRID', (0, 0), (-1, -1), 1, 'black'),  # Garis grid 1px warna hitam
                    ]))
                    prb_tdd_images.append(chart_table_prb_tdd)
                    prb_tdd_images.append(Spacer(1, 5))

                    chart_au_tdd = create_chart_export(hourly4g_balancing[(hourly4g_balancing['SECTOR'] == sector) & (hourly4g_balancing['Band'] == 'L2300')],
                                                f"AU TDD {sector}", 'Active_User')
                    img_bytes_chart_au_tdd = io.BytesIO()
                    chart_au_tdd.write_image(img_bytes_chart_au_tdd, format="png", scale=2)
                    img_bytes_chart_au_tdd.seek(0)
                    chart_table_au_tdd = Table([[Image(img_bytes_chart_au_tdd, width=200, height=130)]], colWidths=220)
                    chart_table_au_tdd.setStyle(TableStyle([
                        ('GRID', (0, 0), (-1, -1), 1, 'black'),  # Garis grid 1px warna hitam
                    ]))
                    au_tdd_images.append(chart_table_au_tdd)
                    au_tdd_images.append(Spacer(1, 5))

            # Menyusun dalam bentuk tabel 3 kolom per baris
            if prb_tdd_images:
                final_chart_layout = Table(
                    [prb_images, au_images, prb_tdd_images, au_tdd_images],  # Atur lebar kolom untuk setiap sektor
                    hAlign='LEFT'
                    )
            else:
                final_chart_layout = Table(
                    [prb_images, au_images],  # Atur lebar kolom untuk setiap sektor
                    hAlign='LEFT'
                    )

            final_chart_layout.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ]))

            elements.append(final_chart_layout)
        pdf.build(elements)
        for file in glob.glob("*.png"):
            os.remove(file)
        return dcc.send_file(pdf_filename)
    return None