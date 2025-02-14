import sqlalchemy
import pyodbc
import pandas as pd
from sqlalchemy.engine import Engine, URL
import joblib
from functools import wraps
import dash
import pandas as pd
from joblib import Memory
from dash import Dash, html, dcc, Input, Output, ctx
from dash import Dash, dcc, html, Input, Output, callback, State, dependencies, no_update, callback_context

dash.register_page(__name__, path=None)

layout = html.Div("This page is a placeholder.")

#layout = None

# Variabel konstan
SERVER = 'rzqhrwdk2l3uxbrcptqo6wanym-g65xipsckyku3pgbyshb3jyejq.datawarehouse.pbidedicated.windows.net'
DATABASE = 'zkpi'
USERNAME = 'purnomo.aji@indottech.corphr.com'
PASSWORD = 'Purn0M012#'
DRIVER = '{ODBC Driver 17 for SQL Server}'
AUTHENTICATION = 'ActiveDirectoryPassword'

memory = Memory(location=None, verbose=0)

@memory.cache
def konek_sql_server():
    try:
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=rzqhrwdk2l3uxbrcptqo6wanym-g65xipsckyku3pgbyshb3jyejq.datawarehouse.pbidedicated.windows.net;"
            "DATABASE=zkpi;"
            "UID=purnomo.aji@indottech.corphr.com;"
            "PWD=Purn0M012#;"
            "Authentication=ActiveDirectoryPassword;"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
        )
        conn = pyodbc.connect(conn_str, timeout=10)
        print("✅ Koneksi ke SQL Server BERHASIL!")
        return conn
    except pyodbc.InterfaceError as e:
        print("❌ InterfaceError: Driver mungkin tidak terinstal dengan benar.")
        print(f"Detail: {e}")
    except pyodbc.OperationalError as e:
        print("❌ OperationalError: Tidak bisa terhubung ke database. Cek firewall atau kredensial.")
        print(f"Detail: {e}")
    except Exception as e:
        print("❌ ERROR tak terduga saat menghubungkan ke SQL Server.")
        print(f"Detail: {e}")
    
    return None


@memory.cache
def dfdail4gnya(slect_site, select_date):
    if not slect_site or not select_date:
        return no_update
    else:
        try:
            engine = konek_sql_server()
            site_filter = ', '.join(map(lambda x: f"'{x}'", set(slect_site)))
            date_filter = ', '.join(map(lambda x: f"'{x}'", set(select_date)))
            query = f"""
            SELECT DISTINCT date, SITEID, ci, Band, Label, Sector_id, Sector_gabung,
            long_grid, lat_grid
            FROM dbo.mdt
            WHERE date = {date_filter}
            AND SITEID IN ({site_filter})
            ORDER BY date, SITEID ASC;
            """

            mdt = pd.read_sql_query(query, engine)
            engine.dispose()
            return mdt.to_dict('records')
        except Exception as e:
            print(f"Error executing query: {e}")
            return no_update
    return no_update


def uniq_site4g(tipe):
    engine = konek_sql_server()
    
    if tipe == 'SITEID':
        query = "SELECT DISTINCT SITEID FROM dbo.daily4g"
    elif tipe == 'DATE_ID':
        query = "SELECT DISTINCT DATE_ID FROM dbo.daily4g"
    else:
        return []
    
    hasil = pd.read_sql_query(query, engine)
    engine.dispose()
    return hasil[tipe].tolist()


def query_daily4g(select_site, start_date, end_date):
    try:
        engine = konek_sql_server()
        site_filter = ', '.join(map(lambda x: f"'{x}'", set(select_site)))

        query = f"""
        SELECT DISTINCT *
        FROM dbo.daily4g
        WHERE DATE_ID BETWEEN '{start_date}' AND '{end_date}'
        AND SITEID IN ({site_filter})
        ORDER BY DATE_ID, EUtranCellTDD ASC;
        """
        daily4g = pd.read_sql_query(query, engine)
        engine.dispose()
        return daily4g.to_dict('records')
    except Exception as e:
        print(f"Error executing query: {e}")
        return no_update

    

# Fungsi untuk mengambil data SITEID
def uniq_sitehourly4g(tipe):
    engine = konek_sql_server()
    if tipe == 'SITEID':
        query = "SELECT DISTINCT SITEID FROM dbo.hourly4g"
    elif tipe == 'DATE_ID':
        query = "SELECT DISTINCT DATE_ID FROM dbo.hourly4g"
    else:
        return []
    hasil = pd.read_sql_query(query, engine)
    engine.dispose()
    if tipe == 'SITEID' and 'SITEID' in hasil.columns:
        hasil = hasil.sort_values(by='SITEID', ascending=True) # Urutkan dari kecil ke besar
    elif tipe == 'DATE_ID' and 'DATE_ID' in hasil.columns:
        hasil = hasil.sort_values(by='DATE_ID', ascending=False) # Urutkan dari besar ke kecil
    return hasil[tipe].tolist()

def query_hourly4g(slect_site, start_date, end_date):
    try:
        engine = konek_sql_server()
        site_filter = ', '.join(map(lambda x: f"'{x}'", set(slect_site)))
        start_date_filter = ', '.join(map(lambda x: f"'{x}'", set(start_date)))
        start_date_filter = ', '.join(map(lambda x: f"'{x}'", set(end_date)))

        query = f"""
        SELECT DISTINCT DATE_ID, hour_id, NEID, Band, SITEID, Sector_gabung, EUtranCellFDD,
        Active_User, DL_Resource_Block_Utilizing_Rate
        FROM dbo.hourly4g
        WHERE DATE_ID BETWEEN '{start_date}' AND '{end_date}'
        AND SITEID IN ({site_filter})
        ORDER BY DATE_ID, hour_id ASC;
        """
        hourly4g = pd.read_sql_query(query, engine)
        engine.dispose()
        return hourly4g.to_dict('records')
    except Exception as e:
        print(f"Error executing query: {e}")
        return no_update



# Fungsi untuk mengambil data SITEID
def uniq_sitemdt(tipe):
    engine = konek_sql_server()
    if tipe == 'SITEID':
        query = "SELECT DISTINCT SITEID FROM dbo.mdt"
    elif tipe == 'date':
        query = "SELECT DISTINCT date FROM dbo.mdt"
    elif tipe == 'Band':
        query = "SELECT DISTINCT Band FROM dbo.mdt"
    else:
        return []
    hasil = pd.read_sql_query(query, engine)
    engine.dispose()
    if tipe == 'date' and 'date' in hasil.columns:
        hasil = hasil.sort_values(by='date', ascending=False)  # Urutkan dari besar ke kecil
    elif tipe == 'SITEID' and 'SITEID' in hasil.columns:
        hasil = hasil.sort_values(by='SITEID', ascending=True)
    elif tipe == 'Band' and 'Band' in hasil.columns:
        hasil = hasil.sort_values(by='Band', ascending=True)
    return hasil[tipe].tolist()

def query_mdt(slect_site, select_date):
    if not slect_site or not select_date:
        return no_update
    else:
        try:
            engine = konek_sql_server()
            site_filter = ', '.join(map(lambda x: f"'{x}'", set(slect_site)))
            date_filter = ', '.join(map(lambda x: f"'{x}'", set(select_date)))
            query = f"""
            SELECT DISTINCT date, SITEID, ci, Band, Label, Sector_id, Sector_gabung,
            long_grid, lat_grid
            FROM dbo.mdt
            WHERE date = {date_filter}
            AND SITEID IN ({site_filter})
            ORDER BY date, SITEID ASC;
            """

            mdt = pd.read_sql_query(query, engine)
            engine.dispose()
            return mdt.to_dict('records')
        except Exception as e:
            print(f"Error executing query: {e}")
            return no_update



# Fungsi untuk mengambil data SITEID
def uniq_siteta(tipe):
    engine = konek_sql_server()
    
    if engine is None:
        print("❌ Gagal Membuat Engine! Koneksi Database Bermasalah.")
        return []

    if tipe == 'Site_id':
        query = "SELECT DISTINCT Site_id FROM dbo.ta"
    elif tipe == 'DATE_ID':
        query = "SELECT DISTINCT DATE_ID FROM dbo.ta"
    elif tipe == 'Band_id':
        query = "SELECT DISTINCT Band_id FROM dbo.ta"
    else:
        return []

    hasil = pd.read_sql_query(query, engine)
    engine.dispose()
    
    return hasil[tipe].tolist()



def query_ta(slect_site, select_band, select_date):
    if not slect_site or not select_band or not select_date:
        return no_update
    else:
        try:
            engine = konek_sql_server()
            site_filter = ', '.join(map(lambda x: f"'{x}'", set(slect_site)))
            date_filter = ', '.join(map(lambda x: f"'{x}'", set(select_date)))
            query = f"""
            SELECT DISTINCT DATE_ID, erbs, EUtranCellFDD, DCVECTOR_INDEX, pmTaInit2Distr, Site_id, NE_id, label, Band_id, Sectoral, Sector_gabung, Distance_km, TA_Index_km, Distance_m, TA_Index_m, dfsum, Occurance, Cumulative_Occurance
            FROM dbo.ta
            WHERE DATE_ID = {date_filter}
            AND Site_id IN ({site_filter})
            ORDER BY DATE_ID, label ASC;
            """

            mdt = pd.read_sql_query(query, engine)
            engine.dispose()
            return mdt.to_dict('records')
        except Exception as e:
            print(f"Error executing query: {e}")
            return no_update
