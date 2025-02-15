import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import date, timedelta
from database import konek_sql_server, query_daily4g, uniq_site4g

# Fungsi utama untuk halaman Monitoring Daily 4G
def monitoring_daily4g_page():
    st.title("Monitoring Daily 4G")

    # Sidebar untuk filter
    st.sidebar.header("Filter")
    select_site = st.sidebar.multiselect("Pilih Site", options=uniq_site4g('SITEID'), default=None)
    select_band = st.sidebar.multiselect("Pilih Band", options=['L1800', 'L900', 'L2100', 'L2300'], default=None)
    date_range = st.sidebar.date_input(
        "Pilih Rentang Tanggal",
        value=(date.today() - timedelta(days=30), date.today()),
        min_value=min(uniq_site4g('DATE_ID')),
        max_value=max(uniq_site4g('DATE_ID'))
    )
    val_slid_mon4g = st.sidebar.slider("Threshold Value", min_value=0, max_value=102, value=0)

    # Validasi input
    if not select_site or not select_band:
        st.warning("Silakan pilih Site dan Band terlebih dahulu.")
        return

    # Query data dari database
    start_date, end_date = date_range
    df_daily4g = query_daily4g(select_site, start_date, end_date)
    qdaily4g = pd.DataFrame(df_daily4g)
    if qdaily4g.empty:
        st.warning("Tidak ada data yang ditemukan untuk filter yang dipilih.")
        return

    # Proses data
    qdaily4g['SECTOR'] = 'Sector ' + qdaily4g['Sector_gabung'].astype(str)
    qdaily4g['label'] = qdaily4g['NEID'] + qdaily4g['EUtranCellTDD'].str[-1:]
    mon_daily_allband = qdaily4g
    mon_daily_allband['label'] = mon_daily_allband['NEID'] + mon_daily_allband['EUtranCellTDD'].str[-1:]

    # Thresholds dan judul
    mon_threshold = ['Threshold_CSSR', 'Threshold_CSSR', 'Threshold_CSSR', 'Threshold_CSSR', 
                     'Threshold_Service_Drop_Rate', 'Threshold_UL_INT_PUSCH', 'Threshold_Intra_Freq_HOSR', 
                     'Threshold_Inter_Freq_HOSR', 'Threshold_CQI', 'Threshold_SE']
    mon_titldaily4g = ['Avail', 'E-Rab', 'RRC', 'SSR', 'SAR', 'UL_INT_PUSCH', 'Intra', 'Inter', 
                       'CQI', 'SE', 'PRB Daily', 'AU Daily', 'Total Payload ', 'Total Payload Site', 
                       'Total Payload NE']

    # Loop untuk membuat grafik
    for mon_x, mon_kpidaily4g in enumerate(['Radio_Network_Availability_Rate', 'ERABSetupSR', 'RRC_ConnSR', 
                                            'CSSR', 'SessionAbnormalRelease', 'UL_INT_PUSCH', 'Intra_FreqHOSR', 
                                            'Inter_FreqHOSR', 'CQI_Bh', 'SE_Bh', 'PRB_Util_DL', 'PRB_Util_UL', 
                                            'Tot_Traff_Vol_Mbyte', 'Total_Payload_site', 'Total_Payload_NE']):
        if mon_kpidaily4g == 'Total_Payload_site':
            mon_dfdaily4g_sum = mon_daily_allband.groupby(['DATE_ID', 'SITEID'], as_index=False)['Tot_Traff_Vol_Mbyte'].sum()
            fig = px.area(mon_dfdaily4g_sum, x='DATE_ID', y=mon_dfdaily4g_sum['Tot_Traff_Vol_Mbyte'] / 1000, 
                          color='SITEID', title=mon_titldaily4g[mon_x] + '(Gb)')
            st.plotly_chart(fig, use_container_width=True)
        elif mon_kpidaily4g == 'Total_Payload_NE':
            mon_dfdaily4g_sum_ne = mon_daily_allband.groupby(['DATE_ID', 'NEID'], as_index=False)['Tot_Traff_Vol_Mbyte'].sum()
            fig = px.area(mon_dfdaily4g_sum_ne, x='DATE_ID', y=mon_dfdaily4g_sum_ne['Tot_Traff_Vol_Mbyte'] / 1000, 
                          color='NEID', title=mon_titldaily4g[mon_x] + '(Gb)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            for mon_sectordaily4g in ['Sector 1', 'Sector 2', 'Sector 3']:
                mon_dfdaily4g = qdaily4g[qdaily4g['Band'].isin(select_band)]
                mon_dfdaily4g = mon_dfdaily4g[mon_dfdaily4g['SECTOR'] == mon_sectordaily4g]
                mon_daily_allband_sector = mon_daily_allband[mon_daily_allband['SECTOR'] == mon_sectordaily4g]

                if mon_kpidaily4g == 'Tot_Traff_Vol_Mbyte':
                    fig = px.bar(mon_daily_allband_sector, x='DATE_ID', y=mon_daily_allband_sector['Tot_Traff_Vol_Mbyte'] / 1000, 
                                 color='label', title=mon_titldaily4g[mon_x] + '_' + mon_sectordaily4g + '(Gb)', barmode='stack')
                elif mon_kpidaily4g in ['PRB_Util_DL', 'PRB_Util_UL']:
                    fig = px.line(mon_daily_allband_sector, x='DATE_ID', y=mon_kpidaily4g, color='label', 
                                  title=mon_titldaily4g[mon_x] + '_' + mon_sectordaily4g)
                else:
                    fig = px.line(mon_dfdaily4g, x='DATE_ID', y=mon_kpidaily4g, color='label', 
                                  title=mon_titldaily4g[mon_x] + '_' + mon_sectordaily4g)
                    fig.add_scatter(x=mon_dfdaily4g['DATE_ID'], y=mon_dfdaily4g[mon_threshold[mon_x]], mode='lines', 
                                    name='Threshold', line=dict(color='firebrick', width=2, dash='dot'))

                st.plotly_chart(fig, use_container_width=True)
