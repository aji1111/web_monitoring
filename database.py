import pandas as pd
import clickhouse_connect
from joblib import Memory
import streamlit as st


memory = Memory(location=None, verbose=0)

@memory.cache
def konek_sql_server():
    conn = clickhouse_connect.get_client(
    host='sswakvljbr.germanywestcentral.azure.clickhouse.cloud',
    user='default',
    password='i.bSsVk68CoYD',
    database='default',
    secure=True
    )
    return conn


def uniq_site4g(tipe):
    engine = konek_sql_server()
    if tipe == 'SITEID':
        query = "SELECT DISTINCT SITEID FROM newdaily4g"
    elif tipe == 'DATE_ID':
        query = "SELECT DISTINCT DATE_ID FROM newdaily4g"
    else:
        return []  
    hasil = engine.query_df(query)
    engine.close()
    return hasil[tipe].tolist()



def query_daily4g(select_site, start_date, end_date):
    try:
        engine = konek_sql_server()
        site_filter = ', '.join(map(lambda x: f"'{x}'", set(select_site)))

        query = f"""
        SELECT DISTINCT *
        FROM newdaily4g
        WHERE DATE_ID BETWEEN '{start_date}' AND '{end_date}'
        AND SITEID IN ({site_filter})
        ORDER BY DATE_ID, EUtranCellTDD ASC;
        """
        daily4g = engine.query_df(query)
        engine.dispose()
        return daily4g.to_dict('records')
    except Exception as e:
        print(f"Error executing query: {e}")
        return no_update

