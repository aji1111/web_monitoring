import streamlit as st

def show_navbar():
    st.sidebar.title("Navigasi")
    page = st.sidebar.radio(
        "Pilih Halaman",
        [
            "HOME",
            "Report to TSEL",
            "Report to EID",
            "Monitoring Daily 4G",
            "Monitoring Hourly 4G",
            "MDT",
            "TA",
            "Export",
        ],
    )
    return page

def main():
    page = show_navbar()

    if page == "HOME":
        from pages.home import home_page
        home_page()
    elif page == "Report to TSEL":
        from pages.report_tsel import report_tsel_page
        report_tsel_page()
    elif page == "Report to EID":
        from pages.report_eid import report_eid_page
        report_eid_page()
    elif page == "Monitoring Daily 4G":
        from pages.monitoring.monitoring_daily4g import monitoring_daily4g_page
        monitoring_daily4g_page()
    elif page == "Monitoring Hourly 4G":
        from pages.monitoring.monitoring_hourly4g import monitoring_hourly4g_page
        monitoring_hourly4g_page()
    elif page == "MDT":
        from pages.mdt import mdt_page
        mdt_page()
    elif page == "TA":
        from pages.ta import ta_page
        ta_page()
    elif page == "Export":
        from pages.export import export_page
        export_page()

if __name__ == "__main__":
    main()
