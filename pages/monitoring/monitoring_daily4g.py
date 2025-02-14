import pyodbc
import pandas as pd
import numpy as np
import sqlalchemy
from sqlalchemy.engine import URL
from dash import Dash, dcc, html, Input, Output, callback, dash_table, clientside_callback
from dash.dash_table.Format import Format, Scheme, Sign, Symbol
#from dash.dash_table import FormatTemplate
from collections import OrderedDict
import plotly.express as px
from datetime import date, datetime, timedelta
import dash_ag_grid as dag
pd.options.mode.chained_assignment = None
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import dash
from cachetools import cached
from database import konek_sql_server, dfdail4gnya, uniq_site4g, query_daily4g


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
dash.register_page(__name__)

layout = html.Div([
    html.Div([
        html.Div([dcc.Dropdown(options = uniq_site4g('SITEID'),id='filter_Site',multi=True,clearable=True)],style={'width': '30%', 'display': 'inline-block'}),
        html.Div([dcc.Dropdown(options = ['L1800', 'L900', 'L2100', 'L2300'],id='filter_Band',multi=True,clearable=True)], style={'width': '30%', 'display': 'inline-block'}),
        html.Div([dcc.DatePickerRange(id="date_range",min_date_allowed=min(uniq_site4g('DATE_ID')),max_date_allowed=max(uniq_site4g('DATE_ID')),start_date=(max(uniq_site4g('DATE_ID'))-timedelta(days=30)),end_date=max(uniq_site4g('DATE_ID')))],style={'fontSize': '6', 'height': '5%', 'width': '39%', 'float': 'right', 'display': 'inline-block'}),
        html.Div([dcc.Slider(id="slider_mon4g", value=0, min=0, max=102, step=1, marks=None)]),
        html.Div(id='chartmonitoring'),
        html.Div(dcc.Store(id="filter-df-store", data=None)),
        html.Div(dcc.Store(id="filter_Site-dropdown", data=None)),
        html.Div(dcc.Store(id="tabs", data=None))
        ], style={'padding': '5px 5px'}),
])

@callback(
    Output('chartmonitoring', 'children', allow_duplicate=True),
    Input('filter_Site', 'value'),
    Input('filter_Band', 'value'),
    Input('date_range', 'start_date'),
    Input('date_range', 'end_date'),
    Input("slider_mon4g", "value"),
    prevent_initial_call=True)
def chartandtable(select_site, select_Band, start_date, end_date, val_slid_mon4g):
    if not select_site or not select_Band:
        return None

    df_daily4g = query_daily4g(select_site, start_date, end_date)
    qdaily4g = pd.DataFrame(df_daily4g)
    qdaily4g['SECTOR'] = 'Sector ' + qdaily4g['Sector_gabung'].astype(str)

    if qdaily4g is None:
        return None
    else:
        if len(qdaily4g) != 0:
            qdaily4g['label'] = qdaily4g['NEID'] + qdaily4g['EUtranCellTDD'].str[-1:]
            mon_daily_allband = qdaily4g
            mon_daily_allband['label'] = mon_daily_allband['NEID'] + mon_daily_allband['EUtranCellTDD'].str[-1:]
            mon_threshold = ['Threshold_CSSR', 'Threshold_CSSR', 'Threshold_CSSR', 'Threshold_CSSR', 'Threshold_Service_Drop_Rate', 'Threshold_UL_INT_PUSCH', 'Threshold_Intra_Freq_HOSR', 'Threshold_Inter_Freq_HOSR', 'Threshold_CQI','Threshold_SE']
            mon_titldaily4g = ['Avail', 'E-Rab', 'RRC', 'SSR', 'SAR', 'UL_INT_PUSCH', 'Intra', 'Inter', 'CQI', 'SE', 'PRB Daily', 'AU Daily', 'Total Payload ', 'Total Payload Site', 'Total Payload NE']
            mon_x = 0
            mon_chartbykpi = []
            mon_chart_sitepay = []
            for mon_kpidaily4g in ['Radio_Network_Availability_Rate', 'ERABSetupSR', 'RRC_ConnSR', 'CSSR', 'SessionAbnormalRelease', 'UL_INT_PUSCH', 'Intra_FreqHOSR', 'Inter_FreqHOSR', 'CQI_Bh', 'SE_Bh', 'PRB_Util_DL', 'PRB_Util_UL', 'Tot_Traff_Vol_Mbyte', 'Total_Payload_site', 'Total_Payload_NE']:
                if mon_kpidaily4g == 'Total_Payload_site':
                    mon_dfdaily4g_sum = mon_daily_allband.groupby(['DATE_ID', 'SITEID'], as_index=False)['Tot_Traff_Vol_Mbyte'].sum()
                    mon_chartdaily4gpay = px.area(x=mon_dfdaily4g_sum['DATE_ID'], y=mon_dfdaily4g_sum['Tot_Traff_Vol_Mbyte']/1000, color=mon_dfdaily4g_sum['SITEID'] , title=mon_titldaily4g[mon_x] + '(Gb)')
                    mon_chartdaily4gpay.update_layout(title_x=0.5, title_y=1, margin={"l": 0, "r": 0, "b": 0, "t": 15}, title_font_color="red", showlegend = True, height = 250, legend=dict(y=0.5), plot_bgcolor='white')
                    mon_chartdaily4gpay.update_layout(legend=dict(orientation = "h", yanchor="top", y=-0.35, xanchor="left", x=0.35, title=None), font=dict(family="Courier", size=10, color="black"))
                    mon_chartdaily4gpay.update_yaxes(range=[0, None], title=None, autorange=True, linecolor='black', gridcolor='lightgrey')
                    mon_chartdaily4gpay.update_xaxes(nticks=40, showgrid=False, title=None, linecolor='black', tickformat="%d/%m/%y", ticklabelmode="period", tickangle=90)
                    mon_chartmonitoringpay = dcc.Graph(figure=mon_chartdaily4gpay, style={"border": "2px black solid", "width": "99.7%", "margin": "2px", "display": "flex", "flex-wrap": "wrap", 'padding': '5px 5px'})
                    mon_chart_sitepay.append(mon_chartmonitoringpay)
                elif mon_kpidaily4g == 'Total_Payload_NE':
                    mon_dfdaily4g_sum_ne = mon_daily_allband.groupby(['DATE_ID', 'NEID'], as_index=False)['Tot_Traff_Vol_Mbyte'].sum()
                    mon_chartdaily4gpay = px.area(x=mon_dfdaily4g_sum_ne['DATE_ID'], y=mon_dfdaily4g_sum_ne['Tot_Traff_Vol_Mbyte']/1000, color=mon_dfdaily4g_sum_ne['NEID'] , title=mon_titldaily4g[mon_x] + '(Gb)')
                    mon_chartdaily4gpay.update_layout(title_x=0.5, title_y=1, margin={"l": 0, "r": 0, "b": 0, "t": 15}, title_font_color="red", showlegend = True, height = 250, legend=dict(y=0.5), plot_bgcolor='white')
                    mon_chartdaily4gpay.update_layout(legend=dict(orientation = "h", yanchor="top", y=-0.35, xanchor="left", x=0.35, title=None), font=dict(family="Courier", size=10, color="black"))
                    mon_chartdaily4gpay.update_yaxes(range=[0, None], title=None, autorange=True, linecolor='black', gridcolor='lightgrey')
                    mon_chartdaily4gpay.update_xaxes(nticks=40, showgrid=False, title=None, linecolor='black', tickformat="%d/%m/%y", ticklabelmode="period", tickangle=90)
                    mon_chartmonitoringpay = dcc.Graph(figure=mon_chartdaily4gpay, style={"border": "2px black solid", "width": "99.7%", "margin": "2px", "display": "flex", "flex-wrap": "wrap", 'padding': '5px 5px'})
                    mon_chart_sitepay.append(mon_chartmonitoringpay)
                else:
                    mon_chart_sector = []
                    for mon_sectordaily4g in ['Sector 1', 'Sector 2', 'Sector 3']:
                        mon_dfdaily4g = qdaily4g[qdaily4g['Band'].isin(select_Band)]
                        mon_dfdaily4g = mon_dfdaily4g[mon_dfdaily4g['SECTOR'] == mon_sectordaily4g]
                        mon_daily_allband_sector = mon_daily_allband[mon_daily_allband['SECTOR'] == mon_sectordaily4g]
                        if mon_kpidaily4g == 'Tot_Traff_Vol_Mbyte':
                            mon_chartdaily4g = px.bar(x=mon_daily_allband_sector['DATE_ID'], y=mon_daily_allband_sector['Tot_Traff_Vol_Mbyte']/1000, color=mon_daily_allband_sector['label'] , title=mon_titldaily4g[mon_x] + '_' + mon_sectordaily4g + '(Gb)', barmode='stack')
                            mon_chartdaily4g.update_layout(title_x=0.5, title_y=1, margin={"l": 0, "r": 0, "b": 0, "t": 15}, title_font_color="red", showlegend = True, height = 250, legend=dict(y=0.5), plot_bgcolor='white')
                            mon_chartdaily4g.update_layout(legend=dict(orientation = "h", yanchor="top", y=-0.35, xanchor="left", x=0.001, title=None), font=dict(family="Courier", size=10, color="black"))
                            mon_chartdaily4g.update_xaxes(nticks=40, showgrid=False, title=None, linecolor='black', tickformat="%d/%m/%y", ticklabelmode="period", tickangle=90)
                            mon_chartdaily4g.update_yaxes(range=[0, None], title=None, autorange=True, linecolor='black', gridcolor='lightgrey')
                            mon_chartmonitoring = dcc.Graph(figure=mon_chartdaily4g, style={"border": "2px black solid", "width": "33%", "margin": "2px", "display": "flex", "flex-wrap": "wrap", 'padding': '5px 5px'})
                            mon_chart_sector.append(mon_chartmonitoring)

                        elif mon_kpidaily4g == 'PRB_Util_DL' or  mon_kpidaily4g == 'PRB_Util_UL':
                            mon_chartdaily4g = px.line(mon_daily_allband_sector, x='DATE_ID', y=mon_kpidaily4g, color='label' , title=mon_titldaily4g[mon_x] + '_' + mon_sectordaily4g)
                            mon_chartdaily4g.update_layout(title_x=0.5, title_y=1, margin={"l": 0, "r": 0, "b": 0, "t": 15}, title_font_color="red", showlegend = True, height = 250, legend=dict(y=0.5), plot_bgcolor='white')
                            mon_chartdaily4g.update_layout(legend=dict(orientation = "h", yanchor="top", y=-0.35, xanchor="left", x=0.001, title=None), font=dict(family="Courier", size=10, color="black"))
                            mon_chartdaily4g.update_xaxes(nticks=40, showgrid=False, title=None, linecolor='black', tickformat="%d/%m/%y", ticklabelmode="period", tickangle=90)
                            mon_chartdaily4g.update_yaxes(range=[0, None], title=None, autorange=True, linecolor='black', gridcolor='lightgrey')
                            mon_chartmonitoring = dcc.Graph(figure=mon_chartdaily4g, style={"border": "2px black solid", "width": "33%", "margin": "2px", "display": "flex", "flex-wrap": "wrap", 'padding': '5px 5px'})
                            mon_chart_sector.append(mon_chartmonitoring)

                        elif mon_kpidaily4g == 'SessionAbnormalRelease' or mon_kpidaily4g == 'CQI_Bh' or mon_kpidaily4g == 'SE_Bh':
                            mon_chartdaily4g = px.line(mon_dfdaily4g, x='DATE_ID', y=mon_kpidaily4g, color='label' , title=mon_titldaily4g[mon_x] + '_' + mon_sectordaily4g)
                            mon_chartdaily4g.add_scatter(x=mon_dfdaily4g['DATE_ID'], y=mon_dfdaily4g[mon_threshold[mon_x]], mode='lines', name='Threshold', line = dict(color='firebrick', width=2, dash='dot'))
                            mon_chartdaily4g.update_layout(title_x=0.5, title_y=1, margin={"l": 0, "r": 0, "b": 0, "t": 15}, title_font_color="red", showlegend = True, height = 250, legend=dict(y=0.5), plot_bgcolor='white')
                            mon_chartdaily4g.update_layout(legend=dict(orientation = "h", yanchor="top", y=-0.35, xanchor="left", x=0.001, title=None), font=dict(family="Courier", size=10, color="black"))
                            mon_chartdaily4g.update_xaxes(nticks=40, showgrid=False, title=None, linecolor='black', tickformat="%d/%m/%y", ticklabelmode="period", tickangle=90)
                            mon_chartdaily4g.update_yaxes(range=[0, 20], title=None, autorange=False, linecolor='black', gridcolor='lightgrey')
                            mon_chartmonitoring = dcc.Graph(figure=mon_chartdaily4g, style={"border": "2px black solid", "width": "33%", "margin": "2px", "display": "flex", "flex-wrap": "wrap", 'padding': '5px 5px'})
                            mon_chart_sector.append(mon_chartmonitoring)

                        elif mon_kpidaily4g == 'UL_INT_PUSCH':
                            mon_chartdaily4g = px.line(mon_dfdaily4g, x='DATE_ID', y=mon_kpidaily4g, color='label' , title=mon_titldaily4g[mon_x] + '_' + mon_sectordaily4g)
                            mon_chartdaily4g.add_scatter(x=mon_dfdaily4g['DATE_ID'], y=mon_dfdaily4g[mon_threshold[mon_x]], mode='lines', name='Threshold', line = dict(color='firebrick', width=2, dash='dot'))
                            mon_chartdaily4g.update_layout(title_x=0.5, title_y=1, margin={"l": 0, "r": 0, "b": 0, "t": 15}, title_font_color="red", showlegend = True, height = 250, legend=dict(y=0.5), plot_bgcolor='white')
                            mon_chartdaily4g.update_layout(legend=dict(orientation = "h", yanchor="top", y=-0.35, xanchor="left", x=0.001, title=None), font=dict(family="Courier", size=10, color="black"))
                            mon_chartdaily4g.update_xaxes(nticks=40, showgrid=False, title=None, linecolor='black', tickformat="%d/%m/%y", ticklabelmode="period", tickangle=90)
                            mon_chartdaily4g.update_yaxes(range=[None, -85], title=None, autorange=True, linecolor='black', gridcolor='lightgrey')
                            mon_chartmonitoring = dcc.Graph(figure=mon_chartdaily4g, style={"border": "2px black solid", "width": "33%", "margin": "2px", "display": "flex", "flex-wrap": "wrap", 'padding': '5px 5px'})
                            mon_chart_sector.append(mon_chartmonitoring)
                        else:
                            mon_chartdaily4g = px.line(mon_dfdaily4g, x='DATE_ID', y=mon_kpidaily4g, color='label' , title=mon_titldaily4g[mon_x] + '_' + mon_sectordaily4g)
                            mon_chartdaily4g.add_scatter(x=mon_dfdaily4g['DATE_ID'], y=mon_dfdaily4g[mon_threshold[mon_x]], mode='lines', name='Threshold', line = dict(color='firebrick', width=2, dash='dot'))
                            mon_chartdaily4g.update_layout(title_x=0.5, title_y=1, margin={"l": 0, "r": 0, "b": 0, "t": 15}, title_font_color="red", showlegend = True, height = 250, legend=dict(y=0.5), plot_bgcolor='white')
                            mon_chartdaily4g.update_layout(legend=dict(orientation = "h", yanchor="top", y=-0.35, xanchor="left", x=0.001, title=None), font=dict(family="Courier", size=10, color="black"))
                            mon_chartdaily4g.update_xaxes(nticks=40, showgrid=False, title=None, linecolor='black', tickformat="%d/%m/%y", ticklabelmode="period", tickangle=90)
                            mon_chartdaily4g.update_yaxes(range=[val_slid_mon4g, 102], title=None, autorange=False, linecolor='black', gridcolor='lightgrey')
                            mon_chartmonitoring = dcc.Graph(figure=mon_chartdaily4g, style={"border": "2px black solid", "width": "33%", "margin": "2px", "display": "flex", "flex-wrap": "wrap", 'padding': '5px 5px'})
                            mon_chart_sector.append(mon_chartmonitoring)
                        
                    mon_chartbykpi.append(html.Div(mon_chart_sector, style={"display": "flex", "flex-wrap": "wrap", "justify-content": "space-between"}))
                mon_x = mon_x + 1
            chartmonitoring = html.Div(mon_chartbykpi + mon_chart_sitepay, style={"padding": "5px 5px"})
            return chartmonitoring
        else:
            return html.Div('Site yang anda Cari Tidak Ada')